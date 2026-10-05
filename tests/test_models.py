import numpy as np
import pandas as pd
import pytest

from ml.models.oil_forecaster import (
    ForecastMetrics,
    ModelComparisonResult,
    MultiHorizonOilForecaster,
    OilPriceForecaster,
)


def _generate_synthetic_oil_series(n_days: int = 300, series: str = "RBRTE", start_price: float = 75.0) -> pd.DataFrame:
    """
    Generates a deterministic synthetic time series for testing the forecasting algorithm.
    Explicitly labeled: FOR UNIT TESTING ONLY.
    """
    np.random.seed(42)
    dates = pd.date_range("2023-01-01", periods=n_days, freq="B")  # Business days
    # Mean-reverting random walk with slight trend
    returns = np.random.normal(loc=0.0002, scale=0.018, size=n_days)
    prices = [start_price]
    for r in returns[1:]:
        prices.append(max(20.0, prices[-1] * (1.0 + r)))

    return pd.DataFrame({
        "period": dates,
        "series": series,
        "value": prices,
        "units": "$/BBL",
        "source": "Synthetic Test Generator",
    })


def test_oil_forecaster_temporal_split_order():
    df = _generate_synthetic_oil_series(n_days=250, series="RBRTE")
    forecaster = OilPriceForecaster(series="RBRTE", horizon_days=7)

    result = forecaster.train_and_evaluate(df, test_size=0.2)

    assert isinstance(result, ModelComparisonResult)
    # Strictly chronological: train_end_date must be before test_start_date
    train_end = pd.to_datetime(result.train_end_date)
    test_start = pd.to_datetime(result.test_start_date)
    test_end = pd.to_datetime(result.test_end_date)

    assert train_end < test_start
    assert test_start <= test_end


def test_oil_forecaster_evaluation_metrics():
    df = _generate_synthetic_oil_series(n_days=250, series="RBRTE")
    forecaster = OilPriceForecaster(series="brent", horizon_days=7)

    result = forecaster.train_and_evaluate(df, test_size=0.2)

    # Validate XGBoost metrics
    assert result.xgboost_metrics.mae > 0
    assert result.xgboost_metrics.rmse > 0
    assert isinstance(result.xgboost_metrics.r2, float)

    # Validate Baseline metrics
    assert result.baseline_metrics.mae > 0
    assert result.baseline_metrics.rmse > 0
    assert isinstance(result.baseline_metrics.r2, float)

    # Check serialization
    res_dict = result.to_dict()
    assert "xgboost" in res_dict
    assert "baseline_persistence" in res_dict
    assert res_dict["series"] == "RBRTE"
    assert res_dict["horizon_days"] == 7


def test_oil_forecaster_out_of_sample_forecast():
    df = _generate_synthetic_oil_series(n_days=250, series="RWTC")
    forecaster = OilPriceForecaster(series="wti", horizon_days=30)

    # Attempting forecast before training must fail
    with pytest.raises(RuntimeError):
        forecaster.forecast(df)

    forecaster.train_and_evaluate(df)
    forecast_output = forecaster.forecast(df)

    assert forecast_output["series"] == "RWTC"
    assert forecast_output["horizon_days"] == 30
    assert "predicted_price" in forecast_output
    assert "current_price" in forecast_output
    assert "forecast_target_date" in forecast_output
    assert forecast_output["predicted_price"] > 0


def test_oil_forecaster_multi_horizons():
    df = _generate_synthetic_oil_series(n_days=350, series="RBRTE")

    for h in [7, 30, 90]:
        forecaster = OilPriceForecaster(series="RBRTE", horizon_days=h)
        eval_result = forecaster.train_and_evaluate(df)
        assert eval_result.horizon_days == h
        assert eval_result.sample_count_test > 0


def test_oil_forecaster_unsupported_params():
    with pytest.raises(ValueError) as exc_horizon:
        OilPriceForecaster(series="RBRTE", horizon_days=14)
    assert "Unsupported horizon" in str(exc_horizon.value)

    with pytest.raises(ValueError) as exc_series:
        OilPriceForecaster(series="NATURAL_GAS", horizon_days=7)
    assert "Unsupported oil series" in str(exc_series.value)


def test_oil_forecaster_insufficient_data():
    tiny_df = _generate_synthetic_oil_series(n_days=30, series="RBRTE")
    forecaster = OilPriceForecaster(series="RBRTE", horizon_days=7)

    with pytest.raises(ValueError) as exc_info:
        forecaster.train_and_evaluate(tiny_df)
    assert "Insufficient historical data" in str(exc_info.value)


def test_multi_horizon_orchestrator():
    brent_df = _generate_synthetic_oil_series(n_days=250, series="RBRTE", start_price=80.0)
    wti_df = _generate_synthetic_oil_series(n_days=250, series="RWTC", start_price=75.0)
    combined = pd.concat([brent_df, wti_df], ignore_index=True)

    orchestrator = MultiHorizonOilForecaster(horizons=[7, 30])
    results = orchestrator.train_and_evaluate_all(combined, series_list=["brent", "wti"])

    assert "RBRTE" in results
    assert "RWTC" in results
    assert 7 in results["RBRTE"]
    assert 30 in results["RBRTE"]

    forecasts = orchestrator.forecast_all(combined, series="brent")
    assert len(forecasts) == 2
    horizons = [f["horizon_days"] for f in forecasts]
    assert 7 in horizons and 30 in horizons
