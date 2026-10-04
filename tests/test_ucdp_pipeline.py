"""
Unit and integration tests for the UCDP data pipeline.
Tests zero-division safety, missing country-month handling, data leakage prevention,
and schema validation.
"""

from pathlib import Path
import numpy as np
import pandas as pd
import pytest

from src.data.config import GW_CODE_TO_ISO3, COUNTRY_NAME_TO_ISO3
from src.data.ucdp_clean import resolve_country_iso3, clean_ucdp_events
from src.data.ucdp_features import (
    safe_relative_growth,
    build_country_month_panel,
    compute_forecasting_features,
    generate_ucdp_features,
)


def test_safe_relative_growth():
    """Verify growth rate calculation is strictly immune to division-by-zero, infs, and NaNs."""
    # Case 1: Both zero
    curr = pd.Series([0.0])
    prev = pd.Series([0.0])
    res = safe_relative_growth(curr, prev)
    assert res.iloc[0] == 0.0

    # Case 2: Zero to positive (jump from zero)
    curr = pd.Series([50.0])
    prev = pd.Series([0.0])
    res = safe_relative_growth(curr, prev)
    assert np.isfinite(res.iloc[0])
    assert not np.isnan(res.iloc[0])
    assert res.iloc[0] > 0.0

    # Case 3: Positive to positive (normal drop)
    curr = pd.Series([5.0])
    prev = pd.Series([10.0])
    res = safe_relative_growth(curr, prev)
    assert res.iloc[0] == -0.5

    # Case 4: Series with edge cases
    curr_series = pd.Series([0, 10, 0, 500, 100])
    prev_series = pd.Series([0, 0, 10, 1, 100])
    res_series = safe_relative_growth(curr_series, prev_series)
    assert not np.isinf(res_series).any()
    assert not res_series.isna().any()


def test_country_iso3_resolution():
    """Verify GW code and country name resolution to ISO 3166-1 alpha-3."""
    # GW code lookup (Algeria = 615 -> DZA)
    row_gw = pd.Series({"country_id": 615, "country": "Algeria"})
    assert resolve_country_iso3(row_gw) == "DZA"

    # Fallback to country name lookup (Colombia = COL)
    row_name = pd.Series({"country_id": None, "country": "Colombia"})
    assert resolve_country_iso3(row_name) == "COL"

    # Unknown entity
    row_unknown = pd.Series({"country_id": 999999, "country": "NonExistentTerritory"})
    assert resolve_country_iso3(row_unknown) is None


def test_missing_country_month_handling():
    """
    Requirement 4: Ensure absence of events is represented as explicit zeros,
    and missing country-month combinations are filled correctly in the Cartesian panel.
    """
    events_data = [
        # Country A has events in Jan and Feb 2020
        {
            "id": 1,
            "country_iso3": "COL",
            "event_date": pd.Timestamp("2020-01-15"),
            "event_year": 2020,
            "best": 10,
            "low": 8,
            "high": 12,
            "deaths_civilians": 2,
            "type_of_violence": 1,
        },
        {
            "id": 2,
            "country_iso3": "COL",
            "event_date": pd.Timestamp("2020-02-10"),
            "event_year": 2020,
            "best": 5,
            "low": 4,
            "high": 6,
            "deaths_civilians": 1,
            "type_of_violence": 2,
        },
        # Country B has an event ONLY in Jan 2020, zero events in Feb and Mar
        {
            "id": 3,
            "country_iso3": "DZA",
            "event_date": pd.Timestamp("2020-01-20"),
            "event_year": 2020,
            "best": 3,
            "low": 2,
            "high": 4,
            "deaths_civilians": 0,
            "type_of_violence": 1,
        },
    ]
    df_events = pd.DataFrame(events_data)
    panel = build_country_month_panel(df_events, min_year=2020, max_year=2020)

    # Full year 2020 has 12 months. With 2 countries: 2 * 12 = 24 rows
    assert len(panel) == 24
    assert set(panel["country_iso3"].unique()) == {"COL", "DZA"}

    # DZA in February 2020 (no events)
    dza_feb = panel[(panel["country_iso3"] == "DZA") & (panel["year_month"] == "2020-02")].iloc[0]
    assert dza_feb["events_total"] == 0
    assert dza_feb["fatalities_best_total"] == 0
    assert dza_feb["has_conflict_event"] == 0
    assert not np.isnan(dza_feb["events_total"])

    # COL in January 2020 (observed event)
    col_jan = panel[(panel["country_iso3"] == "COL") & (panel["year_month"] == "2020-01")].iloc[0]
    assert col_jan["events_total"] == 1
    assert col_jan["fatalities_best_total"] == 10
    assert col_jan["has_conflict_event"] == 1


def test_zero_data_leakage():
    """
    Requirement 9: Features at month t must use only information available at or before t.
    Modifying or appending an event at month t+1 must NOT alter features at month t.
    """
    base_events = [
        {
            "id": 1,
            "country_iso3": "AFG",
            "event_date": pd.Timestamp("2021-01-10"),
            "event_year": 2021,
            "best": 15,
            "low": 10,
            "high": 20,
            "deaths_civilians": 5,
            "type_of_violence": 1,
        },
        {
            "id": 2,
            "country_iso3": "AFG",
            "event_date": pd.Timestamp("2021-02-15"),
            "event_year": 2021,
            "best": 20,
            "low": 15,
            "high": 25,
            "deaths_civilians": 8,
            "type_of_violence": 1,
        },
    ]

    panel_1 = build_country_month_panel(pd.DataFrame(base_events), min_year=2021, max_year=2021)
    feat_1 = compute_forecasting_features(panel_1)

    row_jan_1 = feat_1[(feat_1["country_iso3"] == "AFG") & (feat_1["year_month"] == "2021-01")].iloc[0]
    row_feb_1 = feat_1[(feat_1["country_iso3"] == "AFG") & (feat_1["year_month"] == "2021-02")].iloc[0]

    # Now simulate a massive future event in month 3 (March 2021)
    future_events = base_events + [
        {
            "id": 3,
            "country_iso3": "AFG",
            "event_date": pd.Timestamp("2021-03-25"),
            "event_year": 2021,
            "best": 500,
            "low": 400,
            "high": 600,
            "deaths_civilians": 100,
            "type_of_violence": 1,
        }
    ]

    panel_2 = build_country_month_panel(pd.DataFrame(future_events), min_year=2021, max_year=2021)
    feat_2 = compute_forecasting_features(panel_2)

    row_jan_2 = feat_2[(feat_2["country_iso3"] == "AFG") & (feat_2["year_month"] == "2021-01")].iloc[0]
    row_feb_2 = feat_2[(feat_2["country_iso3"] == "AFG") & (feat_2["year_month"] == "2021-02")].iloc[0]

    # Features for Jan and Feb must be identical despite future event in March!
    feature_cols = [c for c in feat_1.columns if any(
        k in c for k in ["lag", "rolling", "prior", "growth", "fatalities", "events"]
    )]

    for col in feature_cols:
        assert row_jan_1[col] == row_jan_2[col], f"Leakage detected in Jan for column {col}"
        assert row_feb_1[col] == row_feb_2[col], f"Leakage detected in Feb for column {col}"
