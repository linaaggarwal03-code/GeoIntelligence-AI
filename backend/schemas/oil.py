from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class OilForecastResponse(BaseModel):
    series: str = Field(..., description="Oil benchmark series (RBRTE for Brent, RWTC for WTI)")
    horizon_days: int = Field(..., description="Forecast horizon in days (7, 30, 90)")
    current_price: float = Field(..., description="Current observed price ($/BBL)")
    predicted_price: float = Field(..., description="Predicted price at horizon ($/BBL)")
    predicted_return_pct: float = Field(..., description="Predicted percentage return (%)")
    as_of_date: str = Field(..., description="Assessment date (YYYY-MM-DD)")
    forecast_target_date: str = Field(..., description="Target forecast date (YYYY-MM-DD)")
    persistence_baseline_price: float = Field(..., description="Random Walk benchmark price ($/BBL)")


class OilEvaluationMetrics(BaseModel):
    mae: float = Field(..., description="Mean Absolute Error ($/BBL)")
    rmse: float = Field(..., description="Root Mean Squared Error ($/BBL)")
    r2: float = Field(..., description="Coefficient of determination R²")


class OilEvaluationResponse(BaseModel):
    series: str
    horizon_days: int
    train_samples: int
    test_samples: int
    train_end_date: str
    test_start_date: str
    test_end_date: str
    xgboost: OilEvaluationMetrics
    baseline_persistence: OilEvaluationMetrics
    outperformed_baseline: bool


class OilExplanationResponse(BaseModel):
    series: str
    horizon_days: int
    mode: str
    explanation: Dict[str, Any]
