from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from backend.schemas.oil import ModelLimitationsNotice, RankedFeatureItem


class EconomicEvaluationMetrics(BaseModel):
    mae: float = Field(..., description="Mean Absolute Error")
    rmse: float = Field(..., description="Root Mean Squared Error")
    r2: float = Field(..., description="Coefficient of determination R²")


class EconomicBaselineComparison(BaseModel):
    benchmark_type: str = Field("historical_mean_persistence", description="Type of baseline benchmark")
    baseline_value: float = Field(..., description="Historical baseline reference value")
    predicted_impact: float = Field(..., description="Model predicted impact value")
    absolute_difference: float = Field(..., description="Difference from baseline")


class EconomicForecastResponse(BaseModel):
    country: str = Field(..., description="ISO3 country code (e.g. USA, IND, WLD)")
    target_indicator: str = Field(..., description="Target economic impact indicator")
    horizon_days: int = Field(..., description="Impact forecast horizon in days (7, 30, 90)")
    horizon: Optional[str] = Field(None, description="Convenience string formatted horizon (e.g. '30d')")
    predicted_impact_value: float = Field(..., description="Predicted economic impact value")
    predicted_impact: Optional[float] = Field(None, description="Direct alias for predicted impact value")
    baseline_reference_value: float = Field(..., description="Historical baseline rate")
    baseline: Optional[float] = Field(None, description="Direct alias for baseline reference value")
    macro_reporting_year: int = Field(..., description="Latest available published World Bank macro year")
    as_of_date: str = Field(..., description="Assessment date (YYYY-MM-DD)")
    forecast_target_date: str = Field(..., description="Target forecast date (YYYY-MM-DD)")
    model_type: str = Field(..., description="ML estimator used (xgboost or random_forest)")
    baseline_comparison: Optional[EconomicBaselineComparison] = Field(None, description="Comparison vs historical baseline")
    evaluation_metrics: Optional[EconomicEvaluationMetrics] = Field(None, description="Out-of-sample evaluation metrics")
    limitations: Optional[ModelLimitationsNotice] = Field(None, description="Model performance and uncertainty caveats")


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
    base_value: Optional[float] = None
    ranked_features: Optional[List[RankedFeatureItem]] = None
    explanation: Dict[str, Any]
    summary: Optional[str] = None
