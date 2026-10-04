"""
UCDP GED Data Cleaning and Normalization Module.
Loads the raw extracted UCDP GED CSV, validates schema, resolves countries to
ISO 3166-1 alpha-3 standards, sanitizes dates and fatality numbers, and writes
the clean event-level dataset to Parquet.
"""

import logging
from pathlib import Path
from typing import Optional, Set

import numpy as np
import pandas as pd

from src.data.config import (
    RAW_UCDP_DIR,
    RAW_CSV_FILENAME,
    PROCESSED_UCDP_DIR,
    PROCESSED_EVENTS_FILENAME,
    GW_CODE_TO_ISO3,
    COUNTRY_NAME_TO_ISO3,
)

logger = logging.getLogger(__name__)

# Required core columns in UCDP GED 26.1
REQUIRED_RAW_COLUMNS = [
    "id",
    "year",
    "type_of_violence",
    "conflict_name",
    "side_a",
    "side_b",
    "country",
    "country_id",
    "region",
    "date_start",
    "date_end",
    "best",
    "high",
    "low",
    "deaths_civilians",
    "latitude",
    "longitude",
]

VIOLENCE_TYPE_LABELS = {
    1: "state_based",
    2: "non_state",
    3: "one_sided",
}


def resolve_country_iso3(row: pd.Series) -> Optional[str]:
    """
    Resolve country identifier to ISO 3166-1 alpha-3 code.
    First checks the official Gleditsch-Ward country_id, then falls back to country name.
    """
    country_id = row.get("country_id")
    if pd.notna(country_id):
        try:
            gw_code = int(country_id)
            if gw_code in GW_CODE_TO_ISO3:
                return GW_CODE_TO_ISO3[gw_code]
        except (ValueError, TypeError):
            pass

    country_name = str(row.get("country", "")).strip()
    if country_name in COUNTRY_NAME_TO_ISO3:
        return COUNTRY_NAME_TO_ISO3[country_name]

    # Return None if not resolvable
    return None


def clean_ucdp_events(
    raw_csv_path: Optional[Path] = None,
    output_parquet_path: Optional[Path] = None,
) -> pd.DataFrame:
    """
    Load raw UCDP GED CSV, normalize data types, validate coordinates and fatalities,
    standardize country ISO-3 codes, and save to Parquet.
    """
    in_path = raw_csv_path or (RAW_UCDP_DIR / RAW_CSV_FILENAME)
    out_path = output_parquet_path or (PROCESSED_UCDP_DIR / PROCESSED_EVENTS_FILENAME)

    if not in_path.exists():
        raise FileNotFoundError(f"Raw CSV file not found at: {in_path}")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    logger.info("Reading raw UCDP CSV from %s...", in_path)

    # Read CSV with optimized dtypes
    df = pd.read_csv(
        in_path,
        low_memory=False,
        encoding="utf-8",
    )

    # 1. Schema Validation
    missing_cols = [c for c in REQUIRED_RAW_COLUMNS if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Raw dataset is missing required columns: {missing_cols}")

    initial_count = len(df)
    logger.info("Loaded %d raw event records. Commencing cleaning...", initial_count)

    # 2. Date parsing and validation
    # UCDP dates can be 'YYYY-MM-DD' or timestamp strings
    df["date_start_parsed"] = pd.to_datetime(df["date_start"], errors="coerce")
    df["date_end_parsed"] = pd.to_datetime(df["date_end"], errors="coerce")

    # Prefer date_start, fallback to date_end
    df["event_date"] = df["date_start_parsed"].combine_first(df["date_end_parsed"])

    # Fallback to year if exact date cannot be parsed
    invalid_date_mask = df["event_date"].isna()
    if invalid_date_mask.any():
        logger.warning(
            "%d records with unparseable dates; imputing from year column.",
            invalid_date_mask.sum(),
        )
        imputed_dates = pd.to_datetime(
            df.loc[invalid_date_mask, "year"].astype(str) + "-01-01",
            errors="coerce",
        )
        df.loc[invalid_date_mask, "event_date"] = imputed_dates

    # Discard any remaining invalid date records
    df = df.dropna(subset=["event_date"]).copy()
    df["event_year"] = df["event_date"].dt.year
    df["event_month"] = df["event_date"].dt.month
    df["year_month"] = df["event_date"].dt.strftime("%Y-%m")

    # 3. Country ISO-3 Resolution
    logger.info("Resolving country codes to ISO 3166-1 alpha-3...")
    df["country_iso3"] = df.apply(resolve_country_iso3, axis=1)

    unmapped = df[df["country_iso3"].isna()]["country"].unique()
    if len(unmapped) > 0:
        logger.warning("Unmapped country entities (%d): %s", len(unmapped), unmapped)

    # Discard rows where country could not be resolved
    df = df.dropna(subset=["country_iso3"]).copy()

    # 4. Clean numeric fatality and violence metrics
    fatality_cols = ["best", "high", "low", "deaths_civilians", "deaths_a", "deaths_b"]
    for col in fatality_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).clip(lower=0)

    # Type of violence: 1, 2, or 3
    df["type_of_violence"] = (
        pd.to_numeric(df["type_of_violence"], errors="coerce")
        .fillna(0)
        .astype(int)
    )
    df["violence_type_label"] = df["type_of_violence"].map(VIOLENCE_TYPE_LABELS).fillna("unknown")

    # 5. Coordinate sanity
    df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
    df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")
    # Coordinates outside valid earth bounds set to NaN
    coord_mask = (
        (df["latitude"] < -90) | (df["latitude"] > 90) |
        (df["longitude"] < -180) | (df["longitude"] > 180)
    )
    if coord_mask.any():
        df.loc[coord_mask, ["latitude", "longitude"]] = np.nan

    # 6. Deduplicate by event id if present
    if "id" in df.columns:
        df = df.drop_duplicates(subset=["id"]).copy()

    final_count = len(df)
    logger.info(
        "Cleaned dataset: %d records retained (%.1f%% of raw). Writing to %s",
        final_count,
        (final_count / initial_count) * 100,
        out_path,
    )

    # Selected clean schema
    output_cols = [
        "id",
        "country_iso3",
        "country",
        "country_id",
        "region",
        "event_date",
        "event_year",
        "event_month",
        "year_month",
        "type_of_violence",
        "violence_type_label",
        "conflict_name",
        "side_a",
        "side_b",
        "best",
        "high",
        "low",
        "deaths_civilians",
        "latitude",
        "longitude",
    ]
    # Keep only columns that exist
    output_cols = [c for c in output_cols if c in df.columns]
    clean_df = df[output_cols].sort_values(["event_date", "country_iso3"]).reset_index(drop=True)

    clean_df.to_parquet(out_path, index=False, engine="pyarrow", compression="snappy")
    logger.info("Saved clean event dataset to: %s", out_path)
    return clean_df
