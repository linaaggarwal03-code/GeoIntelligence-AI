from typing import Any, Dict
from fastapi import APIRouter, Query

from backend.schemas.oil import (
    OilEvaluationResponse,
    OilExplanationResponse,
    OilForecastResponse,
)
from backend.services.oil_service import oil_service

router = APIRouter(prefix="/api/oil", tags=["Oil Forecasting"])


@router.get(
    "/forecast",
    response_model=OilForecastResponse,
    summary="Get Crude Oil Price Forecast (7/30/90 Days)",
)
def get_oil_forecast(
    series: str = Query("brent", description="Oil benchmark ('brent'/'RBRTE' or 'wti'/'RWTC')"),
    horizon_days: int = Query(30, description="Forecast horizon in days (7, 30, 90)"),
) -> Dict[str, Any]:
    """
    Returns the out-of-sample oil price prediction, expected percentage return,
    and random walk baseline benchmark from the trained XGBoost model.
    """
    return oil_service.get_forecast(series=series, horizon_days=horizon_days)


@router.get(
    "/evaluate",
    response_model=OilEvaluationResponse,
    summary="Evaluate Oil Forecaster against Persistence Baseline",
)
def evaluate_oil_model(
    series: str = Query("brent", description="Oil benchmark ('brent' or 'wti')"),
    horizon_days: int = Query(30, description="Forecast horizon in days (7, 30, 90)"),
) -> Dict[str, Any]:
    """
    Evaluates out-of-sample performance (MAE, RMSE, R²) of the XGBoost forecaster
    against the persistence baseline over chronological test periods.
    """
    return oil_service.get_evaluation(series=series, horizon_days=horizon_days)


@router.get(
    "/explain",
    response_model=OilExplanationResponse,
    summary="Get SHAP Explanations for Oil Price Forecasts",
)
def explain_oil_forecast(
    series: str = Query("brent", description="Oil benchmark ('brent' or 'wti')"),
    horizon_days: int = Query(30, description="Forecast horizon in days (7, 30, 90)"),
    mode: str = Query("local", description="Explanation mode ('local' for instance breakdown, 'global' for feature importance)"),
) -> Dict[str, Any]:
    """
    Generates exact SHAP values detailing feature contributions and rankings
    from the actual trained forecasting model.
    """
    return oil_service.get_explanation(series=series, horizon_days=horizon_days, mode=mode)
