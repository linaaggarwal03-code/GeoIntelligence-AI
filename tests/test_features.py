from datetime import datetime, timedelta
import numpy as np
import pandas as pd
import pytest

from ml.features.oil_features import (
    build_oil_features,
    clean_oil_price_data,
    compute_rsi,
)
from ml.features.economic_features import (
    build_economic_panel,
    clean_worldbank_data,
    engineer_economic_features,
)
from ml.features.shipping_features import (
    MaritimeChokepointObservation,
    ShippingRiskFeaturePipeline,
    clean_trade_flow_data,
    extract_trade_concentration_features,
)


# ---------------------------------------------------------------------------
# Oil Features Tests
# ---------------------------------------------------------------------------

def test_clean_oil_price_data():
    raw_data = pd.DataFrame({
        "period": ["2023-01-03", "2023-01-01", "2023-01-02", "2023-01-02", "bad-date"],
        "series": ["RBRTE", "RBRTE", "RBRTE", "RBRTE", "RBRTE"],
        "value": [80.0, 78.0, 79.0, 79.5, -5.0],  # Duplicate on 2023-01-02, invalid date, negative price
    })

    cleaned = clean_oil_price_data(raw_data)

    assert len(cleaned) == 3
    # Check date sorting
    assert list(cleaned["period"].dt.strftime("%Y-%m-%d")) == ["2023-01-01", "2023-01-02", "2023-01-03"]
    # Check duplicate resolution (keep last: 79.5)
    assert cleaned.loc[cleaned["period"] == "2023-01-02", "value"].iloc[0] == 79.5


def test_oil_feature_calculations():
    # Construct 40 daily observations
    dates = pd.date_range("2023-01-01", periods=40, freq="D")
    prices = [70.0 + i * 0.5 for i in range(40)]
    df = pd.DataFrame({"period": dates, "series": "RBRTE", "value": prices})

    feats = build_oil_features(df, lags=[1, 5], rolling_windows=[7, 14])

    assert "return_1d" in feats.columns
    assert "log_return_1d" in feats.columns
    assert "lag_price_1" in feats.columns
    assert "lag_price_5" in feats.columns
    assert "rolling_mean_7d" in feats.columns
    assert "rolling_volatility_7d" in feats.columns
    assert "macd_line" in feats.columns
    assert "rsi_14" in feats.columns

    # Test lag alignment
    assert np.isnan(feats["lag_price_1"].iloc[0])
    assert feats["lag_price_1"].iloc[1] == feats["value"].iloc[0]
    assert feats["lag_price_5"].iloc[5] == feats["value"].iloc[0]

    # Test return calculation
    expected_ret_1 = (prices[1] - prices[0]) / prices[0]
    assert pytest.approx(feats["return_1d"].iloc[1], 1e-5) == expected_ret_1


def test_oil_features_anti_leakage():
    """
    Verify that altering or adding future data points NEVER alters
    feature values for prior dates (strictly trailing).
    """
    dates = pd.date_range("2023-01-01", periods=30, freq="D")
    prices = [75.0 + np.sin(i / 3.0) for i in range(30)]
    base_df = pd.DataFrame({"period": dates, "series": "RBRTE", "value": prices})

    feats_orig = build_oil_features(base_df, lags=[1, 2], rolling_windows=[7, 14])

    # Now simulate a future scenario where on day 29 the price spikes dramatically
    modified_df = base_df.copy()
    modified_df.loc[29, "value"] = 500.0  # Future shock on last day

    feats_mod = build_oil_features(modified_df, lags=[1, 2], rolling_windows=[7, 14])

    # Up to day 28 (prior to the shock), all feature values must match identically
    for col in ["return_1d", "lag_price_1", "rolling_mean_7d", "rsi_14", "macd_line"]:
        orig_slice = feats_orig.loc[:28, col].dropna()
        mod_slice = feats_mod.loc[:28, col].dropna()
        pd.testing.assert_series_equal(orig_slice, mod_slice, check_exact=False, rtol=1e-6)


# ---------------------------------------------------------------------------
# Economic Features Tests
# ---------------------------------------------------------------------------

def test_clean_worldbank_data():
    raw_df = pd.DataFrame({
        "country_iso3": ["usa", "USA", "usa", "ind"],
        "year": [2021, 2021, 2022, 2022],
        "indicator_id": ["NY.GDP.MKTP.CD", "NY.GDP.MKTP.CD", "NY.GDP.MKTP.CD", "NY.GDP.MKTP.CD"],
        "indicator_name": ["GDP"] * 4,
        "country_name": ["United States", "United States", "United States", "India"],
        "value": [2.3e13, 2.35e13, 2.5e13, 3.1e12],  # Duplicate on USA 2021
    })

    cleaned = clean_worldbank_data(raw_df)
    assert len(cleaned) == 3
    # Check deduplication kept last and upper-cased
    assert (cleaned["country_iso3"] == "USA").sum() == 2
    usa_2021 = cleaned[(cleaned["country_iso3"] == "USA") & (cleaned["year"] == 2021)]
    assert usa_2021["value"].iloc[0] == 2.35e13


def test_build_economic_panel_and_missing_handling():
    raw_df = pd.DataFrame({
        "country_iso3": ["USA", "USA", "USA", "IND", "IND"],
        "year": [2020, 2021, 2022, 2020, 2022],  # Note IND has missing 2021
        "indicator_id": ["FP.CPI.TOTL.ZG"] * 5,
        "indicator_name": ["Inflation"] * 5,
        "country_name": ["USA", "USA", "USA", "India", "India"],
        "value": [1.2, 4.7, 8.0, 6.2, 5.8],
    })

    # 1. Strategy = 'none' (preserves missing observations explicitly)
    panel_none = build_economic_panel(raw_df, impute_strategy="none", add_missing_flags=True)
    assert "inflation_pct" in panel_none.columns
    assert "inflation_pct_is_missing" in panel_none.columns

    # 2. Check derived features
    feats = engineer_economic_features(panel_none)
    assert "inflation_pct_lag1" in feats.columns
    assert "inflation_pct_delta_yoy" in feats.columns
    assert "inflation_pct_rolling_3y_mean" in feats.columns

    # Lag1 for USA in 2021 should be USA 2020 value (1.2)
    usa_2021 = feats[(feats["country_iso3"] == "USA") & (feats["year"] == 2021)]
    assert usa_2021["inflation_pct_lag1"].iloc[0] == 1.2
    assert pytest.approx(usa_2021["inflation_pct_delta_yoy"].iloc[0], 1e-4) == 3.5


def test_economic_features_no_country_leakage():
    """
    Ensure forward fill and lagging never bleed data across different countries.
    """
    raw_df = pd.DataFrame({
        "country_iso3": ["USA", "USA", "IND", "IND"],
        "year": [2020, 2021, 2020, 2021],
        "indicator_id": ["FP.CPI.TOTL.ZG"] * 4,
        "indicator_name": ["Inflation"] * 4,
        "country_name": ["USA", "USA", "India", "India"],
        "value": [2.0, 5.0, 6.0, 7.0],
    })

    panel = build_economic_panel(raw_df, impute_strategy="forward_fill")
    feats = engineer_economic_features(panel)

    # IND in 2020 lag1 must be NaN, NOT USA 2021 value!
    ind_2020 = feats[(feats["country_iso3"] == "IND") & (feats["year"] == 2020)]
    assert pd.isna(ind_2020["inflation_pct_lag1"].iloc[0])


# ---------------------------------------------------------------------------
# Shipping Features Tests
# ---------------------------------------------------------------------------

def test_extract_trade_concentration_hhi():
    # Case 1: 100% concentration from single partner (HHI = 1.0)
    single_partner = pd.DataFrame({
        "period": ["2022"],
        "reporter_iso": ["USA"],
        "partner_iso": ["CAN"],
        "commodity_code": ["2709"],
        "flow_code": ["M"],
        "trade_value_usd": [1000000.0],
        "net_weight_kg": [500000.0],
    })
    hhi_single = extract_trade_concentration_features(single_partner)
    assert len(hhi_single) == 1
    assert hhi_single["hhi_concentration"].iloc[0] == 1.0
    assert hhi_single["partner_count"].iloc[0] == 1

    # Case 2: Even split across two partners (HHI = 0.50)
    dual_partner = pd.DataFrame({
        "period": ["2022", "2022"],
        "reporter_iso": ["USA", "USA"],
        "partner_iso": ["CAN", "MEX"],
        "commodity_code": ["2709", "2709"],
        "flow_code": ["M", "M"],
        "trade_value_usd": [500000.0, 500000.0],
        "net_weight_kg": [250000.0, 250000.0],
    })
    hhi_dual = extract_trade_concentration_features(dual_partner)
    assert len(hhi_dual) == 1
    assert hhi_dual["hhi_concentration"].iloc[0] == 0.50
    assert hhi_dual["partner_count"].iloc[0] == 2


def test_maritime_shipping_pipeline():
    pipeline = ShippingRiskFeaturePipeline()

    obs = [
        MaritimeChokepointObservation(
            chokepoint="STRAIT_OF_HORMUZ",
            date="2024-01-15",
            transit_count=45,
            tanker_volume_barrels=17500000.0,
            average_wait_hours=12.5,
            incident_reported=False,
        ),
        MaritimeChokepointObservation(
            chokepoint="BAB_EL_MANDEB",
            date="2024-01-15",
            transit_count=18,
            incident_reported=True,
        ),
    ]

    df = pipeline.integrate_maritime_observations(obs)
    assert len(df) == 2
    assert "chokepoint" in df.columns
    assert "date" in df.columns
    assert "transit_count" in df.columns
    assert "incident_reported" in df.columns
    assert bool(df.loc[df["chokepoint"] == "BAB_EL_MANDEB", "incident_reported"].iloc[0]) is True
