"""
Orchestrator script for the UCDP Data Pipeline Milestone.
Runs download, cleaning, feature transformation, and validation in sequence.
Provides a unified CLI interface and detailed reporting.
"""

import argparse
import json
import logging
import sys
import time
from pathlib import Path
from typing import Dict, Any

import numpy as np
import pandas as pd

from src.data.config import (
    RAW_UCDP_DIR,
    RAW_ZIP_FILENAME,
    RAW_CSV_FILENAME,
    RAW_METADATA_FILENAME,
    PROCESSED_UCDP_DIR,
    PROCESSED_EVENTS_FILENAME,
    PROCESSED_FEATURES_FILENAME,
    PROCESSED_METADATA_FILENAME,
)
from src.data.ucdp_download import download_ucdp_ged
from src.data.ucdp_clean import clean_ucdp_events
from src.data.ucdp_features import generate_ucdp_features

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("ucdp_pipeline")


def validate_pipeline_outputs() -> Dict[str, Any]:
    """
    Validate all raw and processed outputs for integrity, schema correctness,
    zero-division safety, and completeness.
    """
    logger.info("--- Starting Comprehensive Output Validation ---")
    results: Dict[str, Any] = {"status": "SUCCESS", "checks": {}}

    # 1. Raw Output Checks
    zip_path = RAW_UCDP_DIR / RAW_ZIP_FILENAME
    csv_path = RAW_UCDP_DIR / RAW_CSV_FILENAME
    raw_meta_path = RAW_UCDP_DIR / RAW_METADATA_FILENAME

    assert zip_path.exists(), f"Raw ZIP missing: {zip_path}"
    assert csv_path.exists(), f"Raw CSV missing: {csv_path}"
    assert raw_meta_path.exists(), f"Raw metadata missing: {raw_meta_path}"

    with open(raw_meta_path, "r", encoding="utf-8") as f:
        raw_meta = json.load(f)

    raw_records = raw_meta.get("raw_record_count", 0)
    assert raw_records > 0, "Raw record count in metadata is zero!"
    results["checks"]["raw_files"] = {
        "zip_size_bytes": zip_path.stat().st_size,
        "csv_size_bytes": csv_path.stat().st_size,
        "actual_record_count": raw_records,
        "version": raw_meta.get("dataset_version"),
        "sha256": raw_meta.get("raw_zip_sha256"),
    }

    # 2. Clean Events Parquet Checks
    clean_path = PROCESSED_UCDP_DIR / PROCESSED_EVENTS_FILENAME
    assert clean_path.exists(), f"Clean events Parquet missing: {clean_path}"

    df_clean = pd.read_parquet(clean_path)
    clean_count = len(df_clean)
    assert clean_count > 0, "Clean events dataset is empty!"
    assert "country_iso3" in df_clean.columns, "country_iso3 column missing in clean events!"
    assert not df_clean["country_iso3"].isna().any(), "Found null country_iso3 in clean events!"

    results["checks"]["clean_events"] = {
        "event_count": clean_count,
        "countries_count": int(df_clean["country_iso3"].nunique()),
        "min_date": str(df_clean["event_date"].min()),
        "max_date": str(df_clean["event_date"].max()),
    }

    # 3. Monthly Features Parquet Checks
    features_path = PROCESSED_UCDP_DIR / PROCESSED_FEATURES_FILENAME
    proc_meta_path = PROCESSED_UCDP_DIR / PROCESSED_METADATA_FILENAME
    assert features_path.exists(), f"Features Parquet missing: {features_path}"
    assert proc_meta_path.exists(), f"Processing metadata missing: {proc_meta_path}"

    df_feat = pd.read_parquet(features_path)
    feat_count = len(df_feat)
    assert feat_count > 0, "Features dataset is empty!"

    # Check for NaNs and Infinite values in numeric feature columns
    numeric_cols = df_feat.select_dtypes(include=[np.number]).columns
    nan_cols = [c for c in numeric_cols if df_feat[c].isna().any()]
    inf_cols = [c for c in numeric_cols if np.isinf(df_feat[c]).any()]

    assert len(nan_cols) == 0, f"Found NaNs in feature columns: {nan_cols}"
    assert len(inf_cols) == 0, f"Found infinite values in feature columns: {inf_cols}"

    results["checks"]["monthly_features"] = {
        "total_country_months": feat_count,
        "unique_countries": int(df_feat["country_iso3"].nunique()),
        "start_year_month": str(df_feat["year_month"].min()),
        "end_year_month": str(df_feat["year_month"].max()),
        "total_feature_columns": len(df_feat.columns),
        "zero_nan_check": "PASSED",
        "zero_inf_check": "PASSED",
    }

    logger.info("--- Output Validation PASSED Successfully ---")
    return results


def run_pipeline(
    skip_download: bool = False,
    force_download: bool = False,
    validate_only: bool = False,
) -> Dict[str, Any]:
    """Execute pipeline workflow."""
    start_time = time.time()

    if validate_only:
        return validate_pipeline_outputs()

    # Step 1: Ingestion
    logger.info("=== STEP 1: UCDP Data Ingestion ===")
    if skip_download:
        raw_meta_path = RAW_UCDP_DIR / RAW_METADATA_FILENAME
        if raw_meta_path.exists():
            with open(raw_meta_path, "r", encoding="utf-8") as f:
                raw_metadata = json.load(f)
            logger.info("Skipping download as requested. Using existing metadata.")
        else:
            raw_metadata = download_ucdp_ged(force_download=force_download)
    else:
        raw_metadata = download_ucdp_ged(force_download=force_download)

    # Step 2: Cleaning and Standardization
    logger.info("=== STEP 2: Event Cleaning & ISO Standardization ===")
    clean_df = clean_ucdp_events()

    # Step 3: Feature Engineering
    logger.info("=== STEP 3: Time-Aware Country-Month Panel & Features ===")
    features_df = generate_ucdp_features()

    # Step 4: Validation
    logger.info("=== STEP 4: Output Validation ===")
    validation_results = validate_pipeline_outputs()

    elapsed = time.time() - start_time
    logger.info("=== Pipeline Completed in %.1f seconds ===", elapsed)

    return {
        "status": "SUCCESS",
        "elapsed_seconds": elapsed,
        "raw_metadata": raw_metadata,
        "validation_results": validation_results,
    }


def main():
    parser = argparse.ArgumentParser(description="Run UCDP Geopolitical Data Pipeline")
    parser.add_argument(
        "--skip-download",
        action="store_true",
        help="Skip re-downloading UCDP if local cache exists",
    )
    parser.add_argument(
        "--force-download",
        action="store_true",
        help="Force re-download even if local files are present",
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Only run validation on existing outputs",
    )

    args = parser.parse_args()
    try:
        run_pipeline(
            skip_download=args.skip_download,
            force_download=args.force_download,
            validate_only=args.validate_only,
        )
    except Exception as e:
        logger.exception("Pipeline run failed: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()
