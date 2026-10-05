"""
UCDP Forecasting Feature Pipeline Module.
Transforms normalized event data into a regular, complete country-month panel.
Explicitly accounts for absence of events (zero-filling), guarantees zero data leakage,
computes division-safe growth rates and momentum, and generates rolling/lag features.
"""

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd

from src.data.config import (
    PROCESSED_UCDP_DIR,
    PROCESSED_EVENTS_FILENAME,
    PROCESSED_FEATURES_FILENAME,
    PROCESSED_METADATA_FILENAME,
    LAG_MONTHS,
    ROLLING_WINDOWS,
    PROJECT_ACTIVE_CONFLICT_THRESHOLD,
    MIN_YEAR,
    MAX_YEAR,
)

logger = logging.getLogger(__name__)


def safe_relative_growth(curr: pd.Series, prev: pd.Series) -> pd.Series:
    """
    Compute percentage / relative change safely without division-by-zero or infs.
    - When both curr and prev are 0: growth rate is 0.0
    - When prev is 0 and curr > 0: uses denominator of 1.0 as a baseline increment
    - Infinite or NaN values are replaced with 0.0 and clipped to safe bounds [-10.0, 10.0].
    """
    diff = curr - prev
    # Denominator clipped at lower bound of 1.0 to prevent division by zero
    denom = prev.fillna(0).clip(lower=1.0)
    growth = diff / denom
    growth = growth.replace([np.inf, -np.inf], 0.0).fillna(0.0)
    return growth.clip(lower=-10.0, upper=10.0)


def build_country_month_panel(
    events_df: pd.DataFrame,
    min_year: int = MIN_YEAR,
    max_year: int = MAX_YEAR,
) -> pd.DataFrame:
    """
    Build a complete, balanced Cartesian product panel of (country_iso3 x year_month).
    Absence of events in a country-month is explicitly filled with zeros so that
    peaceful periods are clearly distinguished from missing data.
    """
    # 1. Determine unique countries and full temporal range
    observed_countries = sorted(events_df["country_iso3"].dropna().unique())
    if not observed_countries:
        raise ValueError("No valid country_iso3 found in events dataset.")

    # Determine date range
    actual_min_year = max(min_year, int(events_df["event_year"].min()))
    actual_max_year = min(max_year, int(events_df["event_year"].max()))

    start_date = f"{actual_min_year}-01-01"
    end_date = f"{actual_max_year}-12-01"
    month_starts = pd.date_range(start=start_date, end=end_date, freq="MS")

    logger.info(
        "Constructing full panel across %d countries and %d months (%s to %s)...",
        len(observed_countries),
        len(month_starts),
        actual_min_year,
        actual_max_year,
    )

    # 2. Cartesian product MultiIndex
    full_index = pd.MultiIndex.from_product(
        [observed_countries, month_starts],
        names=["country_iso3", "month_start"],
    )
    panel_df = pd.DataFrame(index=full_index).reset_index()
    panel_df["year"] = panel_df["month_start"].dt.year
    panel_df["month"] = panel_df["month_start"].dt.month
    panel_df["year_month"] = panel_df["month_start"].dt.strftime("%Y-%m")

    # 3. Monthly Aggregations from Cleaned Events
    events_df["month_start"] = pd.to_datetime(
        events_df["event_date"].dt.strftime("%Y-%m-01")
    )

    # Total metrics
    monthly_agg = events_df.groupby(["country_iso3", "month_start"]).agg(
        events_total=("id", "count"),
        fatalities_best_total=("best", "sum"),
        fatalities_low_total=("low", "sum"),
        fatalities_high_total=("high", "sum"),
        fatalities_civilian_total=("deaths_civilians", "sum"),
    ).reset_index()

    # Violence type breakdown
    # 1: State-based, 2: Non-state, 3: One-sided
    for v_code, v_name in [(1, "state_based"), (2, "non_state"), (3, "one_sided")]:
        subset = events_df[events_df["type_of_violence"] == v_code]
        agg_v = subset.groupby(["country_iso3", "month_start"]).agg(
            **{
                f"events_{v_name}": ("id", "count"),
                f"fatalities_{v_name}": ("best", "sum"),
            }
        ).reset_index()
        monthly_agg = monthly_agg.merge(agg_v, on=["country_iso3", "month_start"], how="left")

    # 4. Merge full panel with observed monthly aggregates
    merged_panel = panel_df.merge(
        monthly_agg,
        on=["country_iso3", "month_start"],
        how="left",
    )

    # 5. Explicitly zero-fill non-event months (Absence of conflict != Missing data)
    metric_cols = [
        "events_total",
        "fatalities_best_total",
        "fatalities_low_total",
        "fatalities_high_total",
        "fatalities_civilian_total",
        "events_state_based",
        "fatalities_state_based",
        "events_non_state",
        "fatalities_non_state",
        "events_one_sided",
        "fatalities_one_sided",
    ]
    for col in metric_cols:
        if col in merged_panel.columns:
            merged_panel[col] = merged_panel[col].fillna(0)

    # Binary indicator for whether conflict events occurred in this month
    merged_panel["has_conflict_event"] = (merged_panel["events_total"] > 0).astype(int)

    return merged_panel


def compute_forecasting_features(panel_df: pd.DataFrame) -> pd.DataFrame:
    """
    Generate time-aware, leak-free features for each country across time.
    Features include:
    - Multi-month historical lags (t-1, t-2, t-3, t-6, t-12)
    - Prior rolling window features (t-W ... t-1) strictly prior to month t
    - Trailing rolling window features (up to month t)
    - Safe month-over-month growth rates and logarithmic momentum deltas
    - Project-derived active conflict operationalization indicator
    """
    # Sort chronologically by country and month to ensure temporal ordering
    df = panel_df.sort_values(["country_iso3", "month_start"]).reset_index(drop=True)
    grouped = df.groupby("country_iso3")

    logger.info("Computing multi-horizon lags and rolling features...")

    # A. Historical Lags (Strictly prior periods: t-k)
    for lag in LAG_MONTHS:
        df[f"fatalities_lag_{lag}m"] = grouped["fatalities_best_total"].shift(lag).fillna(0)
        df[f"events_lag_{lag}m"] = grouped["events_total"].shift(lag).fillna(0)

    # B. Prior Rolling Windows (Strictly prior to forecast month: t-1 to t-W)
    # Designed for 1-step ahead forecasting where current month t is not yet observed
    for w in ROLLING_WINDOWS:
        df[f"fatalities_prior_sum_{w}m"] = (
            grouped["fatalities_best_total"]
            .apply(lambda s: s.shift(1).rolling(window=w, min_periods=1).sum())
            .reset_index(level=0, drop=True)
            .fillna(0)
        )
        df[f"events_prior_sum_{w}m"] = (
            grouped["events_total"]
            .apply(lambda s: s.shift(1).rolling(window=w, min_periods=1).sum())
            .reset_index(level=0, drop=True)
            .fillna(0)
        )

    # C. Trailing Rolling Windows (Including month t)
    # Captures current state / baseline trajectory up to observation period t
    for w in ROLLING_WINDOWS:
        df[f"fatalities_rolling_sum_{w}m"] = (
            grouped["fatalities_best_total"]
            .apply(lambda s: s.rolling(window=w, min_periods=1).sum())
            .reset_index(level=0, drop=True)
            .fillna(0)
        )
        df[f"events_rolling_sum_{w}m"] = (
            grouped["events_total"]
            .apply(lambda s: s.rolling(window=w, min_periods=1).sum())
            .reset_index(level=0, drop=True)
            .fillna(0)
        )
        df[f"fatalities_rolling_mean_{w}m"] = (
            grouped["fatalities_best_total"]
            .apply(lambda s: s.rolling(window=w, min_periods=1).mean())
            .reset_index(level=0, drop=True)
            .fillna(0)
        )

    # D. Safe Growth Rates & Momentum (Zero-division safe, clipped)
    prev_fatalities = grouped["fatalities_best_total"].shift(1).fillna(0)
    prev_events = grouped["events_total"].shift(1).fillna(0)

    # Absolute deltas
    df["delta_fatalities_1m"] = df["fatalities_best_total"] - prev_fatalities
    df["delta_events_1m"] = df["events_total"] - prev_events

    # Safe relative growth rates
    df["growth_rate_fatalities_1m"] = safe_relative_growth(df["fatalities_best_total"], prev_fatalities)
    df["growth_rate_events_1m"] = safe_relative_growth(df["events_total"], prev_events)

    # Bounded logarithmic momentum deltas: log(curr + 1) - log(prev + 1)
    df["momentum_fatalities_log_1m"] = (
        np.log1p(df["fatalities_best_total"]) - np.log1p(prev_fatalities)
    )
    df["momentum_events_log_1m"] = (
        np.log1p(df["events_total"]) - np.log1p(prev_events)
    )

    # E. Project-Derived Indicator
    # Operationalization: Flag indicating whether trailing 12-month fatalities >= 25.
    # Note: This is an analytical project definition for escalation threshold monitoring,
    # not an official UCDP classification.
    df["project_active_conflict_indicator"] = (
        df["fatalities_rolling_sum_12m"] >= PROJECT_ACTIVE_CONFLICT_THRESHOLD
    ).astype(int)

    # Convert month_start to string timestamp for storage
    df["month_start"] = df["month_start"].dt.strftime("%Y-%m-%d")

    # Safety checks: ensure zero NaNs and zero infinite values in engineered features
    engineered_cols = [c for c in df.columns if any(
        k in c for k in ["lag", "rolling", "prior", "growth", "momentum", "delta"]
    )]
    for col in engineered_cols:
        if np.isinf(df[col]).any():
            logger.warning("Replacing unexpected infinite values in column %s", col)
            df[col] = df[col].replace([np.inf, -np.inf], 0.0)
        df[col] = df[col].fillna(0.0)

    return df


def generate_ucdp_features(
    clean_events_path: Optional[Path] = None,
    output_features_path: Optional[Path] = None,
    output_metadata_path: Optional[Path] = None,
) -> pd.DataFrame:
    """
    End-to-end execution of the feature pipeline:
    Loads clean events Parquet -> builds complete monthly panel -> computes features -> saves Parquet.
    """
    in_path = clean_events_path or (PROCESSED_UCDP_DIR / PROCESSED_EVENTS_FILENAME)
    out_path = output_features_path or (PROCESSED_UCDP_DIR / PROCESSED_FEATURES_FILENAME)
    meta_path = output_metadata_path or (PROCESSED_UCDP_DIR / PROCESSED_METADATA_FILENAME)

    if not in_path.exists():
        raise FileNotFoundError(f"Clean events Parquet not found at: {in_path}")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    logger.info("Loading cleaned events from: %s", in_path)

    events_df = pd.read_parquet(in_path)
    events_df["event_date"] = pd.to_datetime(events_df["event_date"])

    # 1. Build balanced panel
    panel_df = build_country_month_panel(events_df)

    # 2. Compute leak-free time-aware features
    features_df = compute_forecasting_features(panel_df)

    # 3. Save Parquet
    features_df.to_parquet(out_path, index=False, engine="pyarrow", compression="snappy")
    logger.info("Saved forecasting features panel to: %s", out_path)

    # 4. Write metadata
    unique_countries = int(features_df["country_iso3"].nunique())
    total_country_months = len(features_df)
    date_min = str(features_df["year_month"].min())
    date_max = str(features_df["year_month"].max())

    metadata: Dict[str, Any] = {
        "dataset_name": "UCDP Monthly Country-Level Conflict Features",
        "pipeline_version": "1.0.0",
        "created_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "input_clean_events_path": str(in_path.name),
        "output_features_path": str(out_path.name),
        "total_country_months": total_country_months,
        "unique_countries_count": unique_countries,
        "date_range": {
            "start_year_month": date_min,
            "end_year_month": date_max,
        },
        "feature_columns": list(features_df.columns),
        "division_safety_verified": True,
        "absence_of_events_handled": True,
        "project_derived_threshold": {
            "feature_name": "project_active_conflict_indicator",
            "threshold_deaths_12m": PROJECT_ACTIVE_CONFLICT_THRESHOLD,
            "notes": "Analytical operationalization for forecasting; not an official UCDP definition.",
        },
    }

    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    logger.info(
        "Features metadata written. Panel: %d rows (%d countries x %s to %s).",
        total_country_months,
        unique_countries,
        date_min,
        date_max,
    )
    return features_df
