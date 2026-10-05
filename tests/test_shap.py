import json
import numpy as np
import pandas as pd
import pytest
from sklearn.ensemble import RandomForestRegressor
from xgboost import XGBRegressor

from ml.explainability.shap_explainer import (
    FeatureContribution,
    GlobalExplanation,
    GlobalFeatureImportance,
    LocalExplanation,
    ModelExplainer,
)
from ml.models.oil_forecaster import OilPriceForecaster
from ml.models.economic_impact import EconomicImpactForecaster


def _create_controlled_dataset():
    """
    Creates a simple synthetic dataset where feature_0 dominates the target,
    followed by feature_1, and feature_2 is pure noise.
    """
    np.random.seed(42)
    n = 100
    X = pd.DataFrame({
        "oil_momentum": np.random.normal(0, 1, n),
        "trade_exposure": np.random.uniform(10, 50, n),
        "noise_feature": np.random.normal(0, 0.1, n),
    })
    # y strongly driven by oil_momentum (5x) and trade_exposure (1x)
    y = 5.0 * X["oil_momentum"] + 1.0 * (X["trade_exposure"] / 10.0)
    return X, y


def test_explainer_with_xgboost():
    X, y = _create_controlled_dataset()
    model = XGBRegressor(n_estimators=30, max_depth=3, random_state=42)
    model.fit(X, y)

    explainer = ModelExplainer(model, feature_names=list(X.columns))

    # Global explanation
    glob = explainer.explain_global(X)
    assert isinstance(glob, GlobalExplanation)
    assert len(glob.feature_importances) == 3
    # Top feature must be oil_momentum
    assert glob.feature_importances[0].feature == "oil_momentum"
    assert glob.feature_importances[0].rank == 1

    # Local explanation
    loc = explainer.explain_local(X.iloc[[0]])
    assert isinstance(loc, LocalExplanation)
    assert len(loc.contributions) == 3
    # Sum of SHAP contributions + base_value approx equals prediction
    total_shap = sum(c.shap_value for c in loc.contributions)
    assert pytest.approx(loc.base_value + total_shap, 1e-4) == loc.prediction_value

    # JSON serializability check
    glob_dict = glob.to_dict()
    loc_dict = loc.to_dict()
    assert json.dumps(glob_dict)
    assert json.dumps(loc_dict)


def test_explainer_with_random_forest():
    X, y = _create_controlled_dataset()
    model = RandomForestRegressor(n_estimators=20, max_depth=3, random_state=42)
    model.fit(X, y)

    explainer = ModelExplainer(model, feature_names=list(X.columns))
    glob = explainer.explain_global(X)

    assert len(glob.feature_importances) == 3
    assert glob.feature_importances[0].feature == "oil_momentum"


def test_explainer_unfitted_model_fails():
    model = XGBRegressor()
    with pytest.raises(RuntimeError) as exc_info:
        ModelExplainer(model, feature_names=["f1", "f2"])
    assert "Model is not fitted" in str(exc_info.value)


def test_explainer_missing_features_validation():
    X, y = _create_controlled_dataset()
    model = XGBRegressor(n_estimators=10).fit(X, y)
    explainer = ModelExplainer(model, feature_names=list(X.columns))

    incomplete_X = pd.DataFrame({"oil_momentum": [1.0], "trade_exposure": [20.0]})
    # Missing 'noise_feature'
    with pytest.raises(ValueError) as exc_info:
        explainer.explain_global(incomplete_X)
    assert "missing expected feature columns" in str(exc_info.value)


def test_explainer_empty_input_fails():
    X, y = _create_controlled_dataset()
    model = XGBRegressor(n_estimators=10).fit(X, y)
    explainer = ModelExplainer(model, feature_names=list(X.columns))

    with pytest.raises(ValueError) as exc_info:
        explainer.explain_global(pd.DataFrame())
    assert "empty" in str(exc_info.value)


def test_explainer_with_oil_forecaster_pipeline():
    # Synthetic oil series
    np.random.seed(42)
    dates = pd.date_range("2023-01-01", periods=200, freq="B")
    prices = [75.0]
    for _ in range(199):
        prices.append(max(20.0, prices[-1] * (1.0 + np.random.normal(0.0002, 0.02))))

    oil_df = pd.DataFrame({"period": dates, "series": "RBRTE", "value": prices})

    forecaster = OilPriceForecaster(series="RBRTE", horizon_days=7)
    forecaster.train_and_evaluate(oil_df)

    explainer = ModelExplainer(forecaster)
    assert explainer.feature_names == forecaster.feature_cols

    # Explain latest state
    feat_df = forecaster._prepare_features_and_targets(oil_df)[0]
    sample = feat_df[forecaster.feature_cols].iloc[[-1]]

    loc_exp = explainer.explain_local(sample)
    assert loc_exp.prediction_value is not None
    assert len(loc_exp.contributions) > 0
    assert json.dumps(loc_exp.to_dict())


def test_explainer_with_economic_impact_pipeline():
    from tests.test_economic_impact import (
        _generate_synthetic_macro_data,
        _generate_synthetic_daily_oil,
    )

    macro_df = _generate_synthetic_macro_data(country="USA")
    oil_df = _generate_synthetic_daily_oil(n_days=300, start_date="2021-01-01")

    forecaster = EconomicImpactForecaster(country="USA", horizon_days=30, model_type="xgboost")
    forecaster.train_and_evaluate(macro_df, oil_df)

    explainer = ModelExplainer(forecaster)
    assert explainer.feature_names == forecaster.feature_cols

    aligned = forecaster.build_mixed_frequency_dataset(macro_df, oil_df)
    X, _ = forecaster._generate_target(aligned)
    X_feats = X[forecaster.feature_cols]

    glob = explainer.explain_global(X_feats.head(20))
    assert len(glob.feature_importances) > 0
    assert json.dumps(glob.to_dict())

    loc = explainer.explain_local(X_feats.iloc[[0]])
    assert loc.prediction_value is not None
    assert json.dumps(loc.to_dict())
