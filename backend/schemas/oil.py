from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class OilEvaluationMetrics(BaseModel):
    mae: float = Field(..., description="Mean Absolute Error ($/BBL)")
    rmse: float = Field(..., description="Root Mean Squared Error ($/BBL)")
    r2: float = Field(..., description="Coefficient of determination R²")


class OilBaselineComparison(BaseModel):
    benchmark_type: str = Field("persistence_random_walk", description="Type of baseline benchmark")
    baseline_price: float = Field(..., description="Random Walk benchmark price ($/BBL)")
    predicted_price: float = Field(..., description="Model predicted price ($/BBL)")
    difference_dollars: float = Field(..., description="Difference from baseline ($/BBL)")
    difference_pct: float = Field(..., description="Percentage difference from baseline (%)")


class ModelLimitationsNotice(BaseModel):
    is_deterministic: bool = Field(False, description="Whether forecast is guaranteed (always False)")
    notice: str = Field(
        "Forecasts represent statistical projections under trailing market conditions and should not be interpreted as guaranteed predictions. Energy markets are subject to sudden geopolitical, supply, and macro shocks.",
        description="Scientific limitations and uncertainty notice for frontend display",
    )


class OilForecastResponse(BaseModel):
    series: str = Field(..., description="Oil benchmark series (RBRTE for Brent, RWTC for WTI)")
    commodity: str = Field(..., description="Human-readable commodity name (e.g. Brent Crude Oil, WTI Crude Oil)")
    horizon_days: int = Field(..., description="Forecast horizon in days (7, 30, 90)")
    current_price: float = Field(..., description="Current observed price ($/BBL)")
    predicted_price: float = Field(..., description="Predicted price at horizon ($/BBL)")
    predicted_return_pct: float = Field(..., description="Predicted percentage return (%)")
    projected_return_pct: Optional[float] = Field(None, description="Direct alias for predicted percentage return (%)")
    as_of_date: str = Field(..., description="Assessment date (YYYY-MM-DD)")
    forecast_target_date: str = Field(..., description="Target forecast date (YYYY-MM-DD)")
    persistence_baseline_price: float = Field(..., description="Random Walk benchmark price ($/BBL)")
    baseline_comparison: Optional[OilBaselineComparison] = Field(None, description="Benchmark comparison vs persistence")
    evaluation_metrics: Optional[OilEvaluationMetrics] = Field(None, description="Historical out-of-sample evaluation metrics")
    limitations: Optional[ModelLimitationsNotice] = Field(None, description="Model performance and uncertainty caveats")


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


class RankedFeatureItem(BaseModel):
    rank: int = Field(..., description="Importance or contribution rank")
    feature: str = Field(..., description="Feature variable name")
    importance: float = Field(..., description="SHAP magnitude or contribution")
    direction: Optional[str] = Field("neutral", description="'positive' (pushes up), 'negative' (pushes down), or 'neutral'")
    feature_value: Optional[float] = Field(None, description="Observed value of the feature")


class OilExplanationResponse(BaseModel):
    series: str
    commodity: Optional[str] = None
    horizon_days: int
    mode: str
    base_value: Optional[float] = None
    ranked_features: Optional[List[RankedFeatureItem]] = None
    explanation: Dict[str, Any]
    summary: Optional[str] = None
