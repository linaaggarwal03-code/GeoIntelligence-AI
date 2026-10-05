"""
Explainability Layer for GeoIntelligence AI (Economic & Oil Forecasting Module).

Includes:
- ModelExplainer: Production SHAP explanation engine for tree-based models (XGBoost, Random Forest)
- LocalExplanation, GlobalExplanation, FeatureContribution, GlobalFeatureImportance
"""

from ml.explainability.shap_explainer import (
    FeatureContribution,
    GlobalExplanation,
    GlobalFeatureImportance,
    LocalExplanation,
    ModelExplainer,
)

__all__ = [
    "ModelExplainer",
    "LocalExplanation",
    "GlobalExplanation",
    "FeatureContribution",
    "GlobalFeatureImportance",
]
