from typing import Dict, List, Optional, Union
import numpy as np
import pandas as pd


# Canonical mapping from World Bank indicator IDs to readable feature names
INDICATOR_RENAME_MAP: Dict[str, str] = {
    "NY.GDP.MKTP.CD": "gdp_current_usd",
    "NY.GDP.MKTP.KD.ZG": "gdp_growth_pct",
    "FP.CPI.TOTL.ZG": "inflation_pct",
    "NE.EXP.GNFS.ZS": "exports_pct_gdp",
    "NE.IMP.GNFS.ZS": "imports_pct_gdp",
    "BX.KLT.DINV.WD.GD.ZS": "fdi_net_inflows_pct_gdp",
}


def clean_worldbank_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans raw World Bank observation records.

    - Validates presence of country_iso3, year, indicator_id, and value
    - Casts year to int, value to float
    - Drops duplicates by (country_iso3, year, indicator_id)
    - Preserves provenance (source, indicator_name, country_name)
    """
    if df.empty:
        return pd.DataFrame(columns=[
            "country_iso3", "country_name", "indicator_id", "indicator_name", "year", "value", "source"
        ])

    cleaned = df.copy()

    required_cols = ["country_iso3", "year", "indicator_id", "value"]
    for col in required_cols:
        if col not in cleaned.columns:
            raise ValueError(f"World Bank DataFrame missing required column: '{col}'")

    cleaned["country_iso3"] = cleaned["country_iso3"].astype(str).str.upper().str.strip()
    cleaned["year"] = pd.to_numeric(cleaned["year"], errors="coerce")
    cleaned = cleaned.dropna(subset=["year", "country_iso3"])
    cleaned["year"] = cleaned["year"].astype(int)

    cleaned["value"] = pd.to_numeric(cleaned["value"], errors="coerce")
    cleaned["indicator_id"] = cleaned["indicator_id"].astype(str).str.strip()

    # Deduplicate keeping last observation
    cleaned = cleaned.drop_duplicates(subset=["country_iso3", "year", "indicator_id"], keep="last")
    cleaned = cleaned.sort_values(by=["country_iso3", "year", "indicator_id"]).reset_index(drop=True)

    return cleaned


def build_economic_panel(
    df: pd.DataFrame,
    indicator_map: Optional[Dict[str, str]] = None,
    impute_strategy: str = "none",
    forward_fill_limit: int = 2,
    add_missing_flags: bool = True,
) -> pd.DataFrame:
    """
    Pivots tidy World Bank indicator records into a structured Country-Year panel.

    :param df: Tidy World Bank DataFrame
    :param indicator_map: Optional mapping of indicator IDs to custom feature column names
    :param impute_strategy: Missing value handling ('none', 'forward_fill')
           Never invents observations: 'none' leaves unobserved years as NaN;
           'forward_fill' only carries forward known historical observations up to limit.
    :param forward_fill_limit: Maximum consecutive years to forward-fill
    :param add_missing_flags: Adds '{feature}_is_missing' boolean indicators for transparency
    :return: Country-Year panel DataFrame
    """
    cleaned = clean_worldbank_data(df)
    if cleaned.empty:
        return pd.DataFrame(columns=["country_iso3", "country_name", "year"])

    mapping = indicator_map or INDICATOR_RENAME_MAP

    # Pivot into country-year panel
    pivot = cleaned.pivot_table(
        index=["country_iso3", "year"],
        columns="indicator_id",
        values="value",
        aggfunc="last",
    ).reset_index()

    # Rename indicator columns to readable feature names
    pivot = pivot.rename(columns=mapping)

    # Attach country_name metadata if available
    country_names = (
        cleaned.dropna(subset=["country_name"])
        .drop_duplicates(subset=["country_iso3"])
        .set_index("country_iso3")["country_name"]
        .to_dict()
    )
    pivot["country_name"] = pivot["country_iso3"].map(country_names)

    # Sort strictly chronologically by country
    pivot = pivot.sort_values(by=["country_iso3", "year"]).reset_index(drop=True)

    feature_cols = [c for c in pivot.columns if c not in ["country_iso3", "country_name", "year"]]

    # Transparent missingness tracking
    if add_missing_flags:
        for col in feature_cols:
            pivot[f"{col}_is_missing"] = pivot[col].isna()

    # Explicit imputation handling (if requested)
    if impute_strategy == "forward_fill":
        # Group by country to avoid leaking data across sovereign borders
        filled_features = (
            pivot.groupby("country_iso3")[feature_cols]
            .apply(lambda grp: grp.ffill(limit=forward_fill_limit))
            .reset_index(level=0, drop=True)
        )
        for col in feature_cols:
            pivot[col] = filled_features[col]
    elif impute_strategy != "none":
        raise ValueError(f"Unsupported impute_strategy: '{impute_strategy}'. Use 'none' or 'forward_fill'.")

    return pivot


def engineer_economic_features(panel_df: pd.DataFrame) -> pd.DataFrame:
    """
    Generates macroeconomic derived features from a Country-Year panel:
    - Log GDP & calculated GDP growth YoY
    - Trade openness (% of GDP) = Exports + Imports
    - Trade balance (% of GDP) = Exports - Imports
    - Year-over-Year deltas in inflation and growth
    - Trailing 1-year and 2-year lags
    - Trailing 3-year rolling averages

    Anti-leakage guarantee:
    All calculations are strictly within-country and strictly trailing (shift >= 1 or diff >= 1).
    """
    if panel_df.empty:
        return panel_df

    df = panel_df.sort_values(by=["country_iso3", "year"]).copy()
    country_dfs = []

    for country, grp in df.groupby("country_iso3"):
        c_df = grp.sort_values("year").copy()

        # 1. Macro aggregates
        if "gdp_current_usd" in c_df.columns:
            c_df["log_gdp"] = np.log(c_df["gdp_current_usd"].clip(lower=1.0))
            if "gdp_growth_pct" not in c_df.columns:
                c_df["gdp_growth_pct"] = c_df["gdp_current_usd"].pct_change() * 100.0

        if "exports_pct_gdp" in c_df.columns and "imports_pct_gdp" in c_df.columns:
            c_df["trade_openness_pct_gdp"] = c_df["exports_pct_gdp"] + c_df["imports_pct_gdp"]
            c_df["trade_balance_pct_gdp"] = c_df["exports_pct_gdp"] - c_df["imports_pct_gdp"]

        # 2. YoY Deltas & Trailing Lags
        for feat in ["gdp_growth_pct", "inflation_pct"]:
            if feat in c_df.columns:
                c_df[f"{feat}_delta_yoy"] = c_df[feat].diff(1)
                c_df[f"{feat}_lag1"] = c_df[feat].shift(1)
                c_df[f"{feat}_lag2"] = c_df[feat].shift(2)
                # Trailing 3-year moving average
                c_df[f"{feat}_rolling_3y_mean"] = c_df[feat].rolling(window=3, min_periods=1).mean()

        country_dfs.append(c_df)

    result = pd.concat(country_dfs, ignore_index=True)
    return result.sort_values(by=["country_iso3", "year"]).reset_index(drop=True)
