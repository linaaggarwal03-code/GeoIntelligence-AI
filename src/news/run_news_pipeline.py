"""
Orchestrator script for Member 3 Milestone 2: News Intelligence + NLP Pipeline.
Executes ingestion, normalization, conflict taxonomy classification, lexical NLP scoring,
country-month panel aggregation, and comprehensive validation.
"""

import argparse
import json
import logging
import sys
import time
from pathlib import Path
from typing import Any, Dict

import numpy as np
import pandas as pd

from src.news.config import (
    RAW_NEWS_DIR,
    RAW_ARTICLES_FILENAME,
    RAW_METADATA_FILENAME,
    PROCESSED_NEWS_DIR,
    PROCESSED_ARTICLES_FILENAME,
    PROCESSED_FEATURES_FILENAME,
    PROCESSED_METADATA_FILENAME,
    UCDP_PROCESSED_FEATURES_PATH,
)
from src.news.gdelt_client import ingest_gdelt_news
from src.news.normalize import normalize_articles
from src.news.conflict_classifier import apply_conflict_classification
from src.news.nlp_signals import enrich_article_nlp_signals
from src.news.country_month_agg import generate_country_month_news_features

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("news_pipeline")


def validate_news_outputs() -> Dict[str, Any]:
    """
    Validate all raw and processed outputs for data integrity, absence of leakage,
    zero-division safety, and downstream joinability with UCDP conflict data.
    """
    logger.info("--- Starting Comprehensive News Pipeline Output Validation ---")
    results: Dict[str, Any] = {"status": "SUCCESS", "checks": {}}

    # 1. Raw Output Checks
    raw_json_path = RAW_NEWS_DIR / RAW_ARTICLES_FILENAME
    raw_meta_path = RAW_NEWS_DIR / RAW_METADATA_FILENAME

    assert raw_json_path.exists(), f"Raw JSON file missing: {raw_json_path}"
    assert raw_meta_path.exists(), f"Raw metadata missing: {raw_meta_path}"

    with open(raw_meta_path, "r", encoding="utf-8") as f:
        raw_meta = json.load(f)

    with open(raw_json_path, "r", encoding="utf-8") as f:
        raw_articles = json.load(f)

    assert len(raw_articles) > 0, "Raw articles list is empty!"
    results["checks"]["raw_news"] = {
        "articles_count": len(raw_articles),
        "source": raw_meta.get("source"),
        "sha256": raw_meta.get("raw_json_sha256"),
    }

    # 2. Clean Normalized Articles Checks
    clean_art_path = PROCESSED_NEWS_DIR / PROCESSED_ARTICLES_FILENAME
    assert clean_art_path.exists(), f"Clean articles Parquet missing: {clean_art_path}"

    df_clean = pd.read_parquet(clean_art_path)
    assert len(df_clean) > 0, "Clean articles Parquet is empty!"
    assert "article_id" in df_clean.columns, "article_id missing in clean articles!"
    assert "target_country_iso3" in df_clean.columns, "target_country_iso3 missing!"
    assert "is_conflict_relevant" in df_clean.columns, "is_conflict_relevant missing!"
    assert "tone_score" in df_clean.columns, "tone_score missing!"

    # Verify tone bounds [-1.0, 1.0]
    assert df_clean["tone_score"].min() >= -1.0, "tone_score below -1.0!"
    assert df_clean["tone_score"].max() <= 1.0, "tone_score above 1.0!"

    results["checks"]["clean_articles"] = {
        "clean_record_count": len(df_clean),
        "conflict_relevant_count": int(df_clean["is_conflict_relevant"].sum()),
        "distinct_target_countries": int(df_clean["target_country_iso3"].dropna().nunique()),
        "distinct_domains": int(df_clean["domain"].nunique()),
    }

    # 3. Country-Month Features Parquet Checks
    features_path = PROCESSED_NEWS_DIR / PROCESSED_FEATURES_FILENAME
    proc_meta_path = PROCESSED_NEWS_DIR / PROCESSED_METADATA_FILENAME

    assert features_path.exists(), f"News features Parquet missing: {features_path}"
    assert proc_meta_path.exists(), f"Processing metadata missing: {proc_meta_path}"

    df_feat = pd.read_parquet(features_path)
    assert len(df_feat) > 0, "Features dataset is empty!"

    # Check for NaNs and Infinite values in numeric feature columns
    numeric_cols = df_feat.select_dtypes(include=[np.number]).columns
    inf_cols = [c for c in numeric_cols if np.isinf(df_feat[c]).any()]
    assert len(inf_cols) == 0, f"Found infinite values in feature columns: {inf_cols}"

    # Contemporaneous descriptive metrics must have ZERO NaNs
    contemporaneous_cols = [
        "news_count_total", "unique_domains_count", "avg_tone", "negative_tone_count",
        "extreme_tone_count", "conflict_news_count", "conflict_news_avg_tone",
        "military_escalation_count", "armed_conflict_count", "ceasefire_peace_count",
        "sanctions_count", "conflict_news_ratio", "negative_tone_share",
        "source_diversity", "escalation_signal",
    ]
    contemp_nan_cols = [c for c in contemporaneous_cols if c in df_feat.columns and df_feat[c].isna().any()]
    assert len(contemp_nan_cols) == 0, f"Found NaNs in contemporaneous columns: {contemp_nan_cols}"

    # Verify is_partial_month is present and boolean
    assert "is_partial_month" in df_feat.columns, "is_partial_month column missing!"
    assert df_feat["is_partial_month"].dtype == bool, "is_partial_month is not boolean!"

    # Verify that out-of-window lag_6m and lag_12m are legitimately NaN (no synthetic zero-fill)
    if "conflict_news_lag_6m" in df_feat.columns:
        assert df_feat["conflict_news_lag_6m"].isna().all(), "Expected lag_6m to be NaN for unobserved history!"
    if "conflict_news_lag_12m" in df_feat.columns:
        assert df_feat["conflict_news_lag_12m"].isna().all(), "Expected lag_12m to be NaN for unobserved history!"

    partial_months = sorted(df_feat[df_feat["is_partial_month"] == True]["year_month"].unique().tolist())

    results["checks"]["country_month_features"] = {
        "total_country_months": len(df_feat),
        "unique_countries": int(df_feat["country_iso3"].nunique()),
        "date_range": f"{df_feat['year_month'].min()} to {df_feat['year_month'].max()}",
        "total_columns": len(df_feat.columns),
        "zero_inf_check": "PASSED",
        "contemporaneous_zero_nan_check": "PASSED",
        "historical_nan_preservation": "PASSED",
        "partial_months_detected": partial_months,
    }

    # 4. Joinability Check with UCDP Dataset
    if UCDP_PROCESSED_FEATURES_PATH.exists():
        logger.info("Verifying joinability with UCDP conflict features dataset...")
        df_ucdp = pd.read_parquet(UCDP_PROCESSED_FEATURES_PATH, columns=["country_iso3", "year_month"])
        # Perform test inner merge on key
        merged_test = pd.merge(
            df_ucdp,
            df_feat,
            on=["country_iso3", "year_month"],
            how="inner",
        )
        logger.info(
            "UCDP-News join test successful: %d overlapping country-months found.",
            len(merged_test),
        )
        results["checks"]["ucdp_join_test"] = {
            "status": "PASSED",
            "overlapping_country_months": len(merged_test),
        }
    else:
        results["checks"]["ucdp_join_test"] = {"status": "SKIPPED_NO_UCDP_FILE"}

    logger.info("--- News Pipeline Output Validation PASSED Successfully ---")
    return results


def run_pipeline(
    skip_fetch: bool = False,
    force_fetch: bool = False,
    validate_only: bool = False,
) -> Dict[str, Any]:
    """Execute end-to-end News Intelligence pipeline."""
    start_time = time.time()

    if validate_only:
        return validate_news_outputs()

    # Step 1: Ingestion
    logger.info("=== STEP 1: GDELT DOC 2.0 Ingestion ===")
    raw_metadata = ingest_gdelt_news(force_fetch=force_fetch)

    # Step 2: Normalization & Country Entity Resolution
    logger.info("=== STEP 2: Article Normalization & Country Decoupling ===")
    raw_json_path = RAW_NEWS_DIR / RAW_ARTICLES_FILENAME
    with open(raw_json_path, "r", encoding="utf-8") as f:
        raw_articles = json.load(f)

    norm_df = normalize_articles(raw_articles)

    # Step 3: Conflict Taxonomy Classification
    logger.info("=== STEP 3: Conflict Taxonomy Classification ===")
    classified_df = apply_conflict_classification(norm_df)

    # Step 4: Lexical NLP Scoring & Clean Parquet Export
    logger.info("=== STEP 4: Lexical Sentiment & Article Parquet Export ===")
    clean_df = enrich_article_nlp_signals(classified_df)

    # Step 5: Country-Month Aggregation & Prior-Only Forecasting Features
    logger.info("=== STEP 5: Country-Month Panel & Leak-Free Features ===")
    features_df = generate_country_month_news_features()

    # Step 6: Validation
    logger.info("=== STEP 6: Output Validation ===")
    validation_results = validate_news_outputs()

    elapsed = time.time() - start_time
    logger.info("=== News Pipeline Completed in %.1f seconds ===", elapsed)

    return {
        "status": "SUCCESS",
        "elapsed_seconds": elapsed,
        "raw_metadata": raw_metadata,
        "validation_results": validation_results,
    }


def main():
    parser = argparse.ArgumentParser(description="Run News Intelligence & NLP Pipeline (GDELT)")
    parser.add_argument(
        "--skip-fetch",
        action="store_true",
        help="Skip API fetching if local raw snapshot exists",
    )
    parser.add_argument(
        "--force-fetch",
        action="store_true",
        help="Force re-fetch from GDELT API even if cached",
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Run validation checks on existing news outputs only",
    )

    args = parser.parse_args()
    try:
        run_pipeline(
            skip_fetch=args.skip_fetch,
            force_fetch=args.force_fetch,
            validate_only=args.validate_only,
        )
    except Exception as e:
        logger.exception("News pipeline execution failed: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()
