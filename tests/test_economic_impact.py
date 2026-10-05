import numpy as np
import pandas as pd
import pytest

from ml.models.economic_impact import (
    EconomicImpactForecaster,
    EconomicModelComparisonResult,
    SUPPORTED_ECONOMIC_HORIZONS,
)


def _generate_synthetic_macro_data(country: str = "USA") -> pd.DataFrame:
    """
    Generates annual macroeconomic indicators for testing.
    FOR TESTING ONLY.
    """
    years = list(range(2015, 2024))
    records = []
    for y in years:
        records.extend([
            {
                "country_iso3": country,
                "country_name": "United States",
                "indicator_id": "NY.GDP.MKTP.CD",
                "indicator_name": "GDP",
                "year": y,
                "value": 1.8e13 + (y - 2015) * 8e11,
                "source": "World Bank Test",
            },
            {
                "country_iso3": country,
                "country_name": "United States",
                "indicator_id": "FP.CPI.TOTL.ZG",
                "indicator_name": "Inflation",
                "year": y,
                "value": 1.5 + (y % 4) * 1.2,
                "source": "World Bank Test",
            },
            {
                "country_iso3": country,
                "country_name": "United States",
                "indicator_id": "NE.EXP.GNFS.ZS",
                "indicator_name": "Exports % GDP",
                "year": y,
                "value": 11.5 + (y % 3) * 0.5,
                "source": "World Bank Test",
            },
            {
                "country_iso3": country,
                "country_name": "United States",
                "indicator_id": "NE.IMP.GNFS.ZS",
                "indicator_name": "Imports % GDP",
                "year": y,
                "value": 14.5 + (y % 3) * 0.4,
                "source": "World Bank Test",
            },
        ])
    return pd.DataFrame(records)


def _generate_synthetic_daily_oil(n_days: int = 400, start_date: str = "2020-01-01") -> pd.DataFrame:
    """
    Generates daily oil price time series spanning multiple years for testing.
    FOR TESTING ONLY.
    """
    np.random.seed(42)
    dates = pd.date_range(start_date, periods=n_days, freq="B")
    prices = [70.0]
    for _ in range(n_days - 1):
        ret = np.random.normal(0.0003, 0.02)
        prices.append(max(20.0, prices[-1] * (1.0 + ret)))

    return pd.DataFrame({
        "period": dates,
        "series": "RBRTE",
        "value": prices,
        "units": "$/BBL",
        "source": "Synthetic Oil Test",
    })


def test_mixed_frequency_alignment():
    macro_df = _generate_synthetic_macro_data(country="USA")
    oil_df = _generate_synthetic_daily_oil(n_days=300, start_date="2021-01-01")

    forecaster = EconomicImpactForecaster(country="USA", horizon_days=30)
    aligned = forecaster.build_mixed_frequency_dataset(macro_df, oil_df)

    assert not aligned.empty
    assert "period" in aligned.columns
    assert "macro_reporting_year" in aligned.columns
    assert "energy_shock_exposure" in aligned.columns
    assert "supply_chain_vulnerability" in aligned.columns

    # Publication lag verification: macro reporting year must always be < oil observation year
    for _, row in aligned.iterrows():
        assert row["macro_reporting_year"] < row["period"].year


def test_economic_impact_temporal_split():
    macro_df = _generate_synthetic_macro_data(country="USA")
    oil_df = _generate_synthetic_daily_oil(n_days=350, start_date="2021-01-01")

    forecaster = EconomicImpactForecaster(country="USA", horizon_days=30, model_type="xgboost")
    result = forecaster.train_and_evaluate(macro_df, oil_df, test_size=0.2)

    assert isinstance(result, EconomicModelComparisonResult)
    train_end = pd.to_datetime(result.train_end_period)
    test_start = pd.to_datetime(result.test_start_period)

    # Strictly chronological
    assert train_end < test_start
    assert result.sample_count_train > 0
    assert result.sample_count_test > 0


def test_economic_impact_evaluation_metrics():
    macro_df = _generate_synthetic_macro_data(country="USA")
    oil_df = _generate_synthetic_daily_oil(n_days=350, start_date="2021-01-01")

    forecaster = EconomicImpactForecaster(country="USA", horizon_days=7, model_type="xgboost")
    result = forecaster.train_and_evaluate(macro_df, oil_df)

    assert result.ml_metrics.mae > 0
    assert result.ml_metrics.rmse > 0
    assert isinstance(result.ml_metrics.r2, float)

    assert result.baseline_metrics.mae > 0
    assert result.baseline_metrics.rmse > 0

    res_dict = result.to_dict()
    assert res_dict["country"] == "USA"
    assert res_dict["horizon_days"] == 7
    assert "ml_model" in res_dict
    assert "baseline" in res_dict


def test_economic_impact_forecast_out_of_sample():
    macro_df = _generate_synthetic_macro_data(country="USA")
    oil_df = _generate_synthetic_daily_oil(n_days=350, start_date="2021-01-01")

    forecaster = EconomicImpactForecaster(country="USA", horizon_days=30, model_type="random_forest")

    with pytest.raises(RuntimeError):
        forecaster.forecast_impact(macro_df, oil_df)

    forecaster.train_and_evaluate(macro_df, oil_df)
    forecast = forecaster.forecast_impact(macro_df, oil_df)

    assert forecast["country"] == "USA"
    assert forecast["horizon_days"] == 30
    assert "predicted_impact_value" in forecast
    assert "forecast_target_date" in forecast
    assert forecast["model_type"] == "random_forest"


def test_economic_impact_multi_horizons():
    macro_df = _generate_synthetic_macro_data(country="USA")
    oil_df = _generate_synthetic_daily_oil(n_days=400, start_date="2021-01-01")

    for h in [7, 30, 90]:
        forecaster = EconomicImpactForecaster(country="USA", horizon_days=h)
        eval_res = forecaster.train_and_evaluate(macro_df, oil_df)
        assert eval_res.horizon_days == h
        assert eval_res.sample_count_test > 0


def test_economic_impact_unsupported_params():
    with pytest.raises(ValueError) as exc_h:
        EconomicImpactForecaster(country="USA", horizon_days=14)
    assert "Unsupported horizon" in str(exc_h.value)

    with pytest.raises(ValueError) as exc_m:
        EconomicImpactForecaster(country="USA", horizon_days=30, model_type="linear_regression")
    assert "Unsupported model_type" in str(exc_m.value)


def test_economic_impact_missing_country_data():
    macro_df = _generate_synthetic_macro_data(country="USA")
    oil_df = _generate_synthetic_daily_oil(n_days=300, start_date="2021-01-01")

    # Asking for a country not in macro_df
    forecaster = EconomicImpactForecaster(country="FRA", horizon_days=30)
    with pytest.raises(ValueError) as exc_info:
        forecaster.train_and_evaluate(macro_df, oil_df)
    assert "No macroeconomic records found for country 'FRA'" in str(exc_info.value)
