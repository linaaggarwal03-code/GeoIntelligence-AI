from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class EconomicForecastResponse(BaseModel):
    country: str = Field(..., description="ISO3 country code (e.g. USA, IND, WLD)")
    target_indicator: str = Field(..., description="Target economic impact indicator")
    horizon_days: int = Field(..., description="Impact forecast horizon in days (7, 30, 90)")
    predicted_impact_value: float = Field(..., description="Predicted economic impact value")
    baseline_reference_value: float = Field(..., description="Historical baseline rate")
    macro_reporting_year: int = Field(..., description="Latest available published World Bank macro year")
    as_of_date: str = Field(..., description="Assessment date (YYYY-MM-DD)")
    forecast_target_date: str = Field(..., description="Target forecast date (YYYY-MM-DD)")
    model_type: str = Field(..., description="ML estimator used (xgboost or random_forest)")


class EconomicEvaluationMetrics(BaseModel):
    mae: float = Field(..., description="Mean Absolute Error")
    rmse: float = Field(..., description="Root Mean Squared Error")
    r2: float = Field(..., description="Coefficient of determination R²")


class EconomicEvaluationResponse(BaseModel):
    country: str
    target_indicator: str
    horizon_days: int
    model_type: str
    train_samples: int
    test_samples: int
    train_end_period: str
    test_start_period: str
    test_end_period: str
    ml_model: EconomicEvaluationMetrics
    baseline: EconomicEvaluationMetrics
    outperformed_baseline: bool


class EconomicExplanationResponse(BaseModel):
    country: str
    target_indicator: str
    horizon_days: int
    mode: str
    explanation: Dict[str, Any]
