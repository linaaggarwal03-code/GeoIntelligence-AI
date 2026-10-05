import numpy as np
import pandas as pd
import pytest

from ml.models.economic_impact import EconomicImpactForecaster
from ml.models.oil_forecaster import OilPriceForecaster
from ml.scenarios.what_if_engine import ScenarioResult, WhatIfEngine
from tests.test_economic_impact import (
    _generate_synthetic_daily_oil,
    _generate_synthetic_macro_data,
)


def _generate_synthetic_oil_series(n_days: int = 250) -> pd.DataFrame:
    np.random.seed(42)
    dates = pd.date_range("2023-01-01", periods=n_days, freq="B")
    prices = [75.0]
    for _ in range(n_days - 1):
        prices.append(max(20.0, prices[-1] * (1.0 + np.random.normal(0.0002, 0.018))))
    return pd.DataFrame({"period": dates, "series": "RBRTE", "value": prices})


def test_oil_baseline_scenario():
    oil_df = _generate_synthetic_oil_series()
    forecaster = OilPriceForecaster(series="RBRTE", horizon_days=30)
    forecaster.train_and_evaluate(oil_df)

    engine = WhatIfEngine()
    result = engine.simulate_oil_scenario(forecaster, oil_df, scenario_name="baseline")

    assert isinstance(result, ScenarioResult)
    assert result.scenario_name == "baseline"
    assert result.horizon_days == 30
    assert pytest.approx(result.scenario_forecast, 1e-4) == result.baseline_forecast
    assert pytest.approx(result.absolute_difference, 1e-4) == 0.0
    assert pytest.approx(result.percentage_difference, 1e-4) == 0.0


def test_oil_positive_and_negative_shocks():
    oil_df = _generate_synthetic_oil_series()
    forecaster = OilPriceForecaster(series="RBRTE", horizon_days=30)
    forecaster.train_and_evaluate(oil_df)

    engine = WhatIfEngine()

    pos_res = engine.simulate_oil_scenario(forecaster, oil_df, scenario_name="positive_oil_shock")
    neg_res = engine.simulate_oil_scenario(forecaster, oil_df, scenario_name="negative_oil_shock")

    # Positive shock should produce higher forecast price than negative shock
    assert pos_res.scenario_forecast > neg_res.scenario_forecast
    assert pos_res.absolute_difference != 0.0
    assert len(pos_res.changed_input_features) > 0
    assert len(neg_res.changed_input_features) > 0


def test_oil_custom_scenario():
    oil_df = _generate_synthetic_oil_series()
    forecaster = OilPriceForecaster(series="RBRTE", horizon_days=7)
    forecaster.train_and_evaluate(oil_df)

    engine = WhatIfEngine()
    custom_mods = {
        "return_5d": 0.12,
        "rolling_volatility_30d": 0.45,
    }
    result = engine.simulate_oil_scenario(
        forecaster, oil_df, scenario_name="custom", modifications=custom_mods
    )

    assert result.scenario_name == "custom"
    assert "return_5d" in result.changed_input_features
    assert "rolling_volatility_30d" in result.changed_input_features
    assert result.changed_input_features["return_5d"]["scenario"] == 0.12


def test_oil_scenario_invalid_inputs():
    oil_df = _generate_synthetic_oil_series()
    forecaster = OilPriceForecaster(series="RBRTE", horizon_days=7)
    forecaster.train_and_evaluate(oil_df)

    engine = WhatIfEngine()

    # 1. Unknown feature name
    with pytest.raises(ValueError) as exc_unknown:
        engine.simulate_oil_scenario(forecaster, oil_df, scenario_name="custom", modifications={"fake_feature": 1.0})
    assert "Unknown scenario feature" in str(exc_unknown.value)

    # 2. Negative oil price
    with pytest.raises(ValueError) as exc_price:
        engine.simulate_oil_scenario(forecaster, oil_df, scenario_name="custom", modifications={"oil_price": -10.0})
    assert "strictly positive" in str(exc_price.value)

    # 3. Negative volatility
    with pytest.raises(ValueError) as exc_vol:
        engine.simulate_oil_scenario(forecaster, oil_df, scenario_name="custom", modifications={"rolling_volatility_30d": -0.5})
    assert "cannot be negative" in str(exc_vol.value)


def test_economic_impact_scenarios():
    macro_df = _generate_synthetic_macro_data(country="USA")
    oil_df = _generate_synthetic_daily_oil(n_days=300, start_date="2021-01-01")

    forecaster = EconomicImpactForecaster(country="USA", horizon_days=30, model_type="xgboost")
    forecaster.train_and_evaluate(macro_df, oil_df)

    engine = WhatIfEngine()

    # Baseline scenario
    base_res = engine.simulate_economic_scenario(forecaster, macro_df, oil_df, scenario_name="baseline")
    assert pytest.approx(base_res.scenario_forecast, 1e-4) == base_res.baseline_forecast

    # Positive oil shock
    shock_res = engine.simulate_economic_scenario(forecaster, macro_df, oil_df, scenario_name="positive_oil_shock")
    assert shock_res.target_type == "economic_impact"
    assert "oil_return_20d" in shock_res.changed_input_features

    # Supply chain crisis
    crisis_res = engine.simulate_economic_scenario(forecaster, macro_df, oil_df, scenario_name="supply_chain_crisis")
    assert "trade_hhi" in crisis_res.changed_input_features
    assert crisis_res.changed_input_features["trade_hhi"]["scenario"] > crisis_res.changed_input_features["trade_hhi"]["baseline"]


def test_economic_scenario_invalid_hhi():
    macro_df = _generate_synthetic_macro_data(country="USA")
    oil_df = _generate_synthetic_daily_oil(n_days=300, start_date="2021-01-01")

    forecaster = EconomicImpactForecaster(country="USA", horizon_days=30)
    forecaster.train_and_evaluate(macro_df, oil_df)

    engine = WhatIfEngine()

    # HHI > 1.0 must be rejected
    with pytest.raises(ValueError) as exc_hhi:
        engine.simulate_economic_scenario(forecaster, macro_df, oil_df, scenario_name="custom", modifications={"trade_hhi": 1.5})
    assert "Trade concentration (HHI) must be in [0.0, 1.0]" in str(exc_hhi.value)


def test_scenario_multiple_horizons():
    oil_df = _generate_synthetic_oil_series(n_days=300)
    engine = WhatIfEngine()

    for h in [7, 30, 90]:
        forecaster = OilPriceForecaster(series="RBRTE", horizon_days=h)
        forecaster.train_and_evaluate(oil_df)
        res = engine.simulate_oil_scenario(forecaster, oil_df, scenario_name="positive_oil_shock")
        assert res.horizon_days == h
        assert res.scenario_forecast > 0


def test_scenario_determinism():
    oil_df = _generate_synthetic_oil_series()
    forecaster = OilPriceForecaster(series="RBRTE", horizon_days=30)
    forecaster.train_and_evaluate(oil_df)

    engine = WhatIfEngine()
    mods = {"return_20d": 0.20, "rolling_volatility_30d": 0.40}

    run1 = engine.simulate_oil_scenario(forecaster, oil_df, scenario_name="custom", modifications=mods)
    run2 = engine.simulate_oil_scenario(forecaster, oil_df, scenario_name="custom", modifications=mods)

    assert run1.scenario_forecast == run2.scenario_forecast
    assert run1.absolute_difference == run2.absolute_difference
    assert run1.to_dict() == run2.to_dict()
