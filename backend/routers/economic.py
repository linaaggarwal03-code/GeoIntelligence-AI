from typing import Any, Dict
from fastapi import APIRouter, Query

from backend.schemas.economic import (
    EconomicEvaluationResponse,
    EconomicExplanationResponse,
    EconomicForecastResponse,
)
from backend.services.economic_service import economic_service

router = APIRouter(prefix="/api/economic", tags=["Economic Impact Forecasting"])


@router.get(
    "/forecast",
    response_model=EconomicForecastResponse,
    summary="Get Mixed-Frequency Economic Impact Forecast (7/30/90 Days)",
)
def get_economic_impact_forecast(
    country: str = Query("USA", description="ISO3 country code (e.g. USA, IND, WLD)"),
    horizon_days: int = Query(30, description="Forecast horizon in days (7, 30, 90)"),
    indicator: str = Query("inflation_impact_pct", description="Target economic indicator"),
) -> Dict[str, Any]:
    """
    Returns the out-of-sample forward macroeconomic impact prediction
    derived from high-frequency energy transmission and annual macro fundamentals.
    """
    return economic_service.get_forecast(
        country=country,
        horizon_days=horizon_days,
        target_indicator=indicator,
    )


@router.get(
    "/evaluate",
    response_model=EconomicEvaluationResponse,
    summary="Evaluate Economic Impact Model against Historical Baseline",
)
def evaluate_economic_impact_model(
    country: str = Query("USA", description="ISO3 country code"),
    horizon_days: int = Query(30, description="Forecast horizon in days (7, 30, 90)"),
    indicator: str = Query("inflation_impact_pct", description="Target economic indicator"),
) -> Dict[str, Any]:
    """
    Evaluates out-of-sample performance (MAE, RMSE, R²) of the economic impact model
    against the persistence historical baseline.
    """
    return economic_service.get_evaluation(
        country=country,
        horizon_days=horizon_days,
        target_indicator=indicator,
    )


@router.get(
    "/explain",
    response_model=EconomicExplanationResponse,
    summary="Get SHAP Explanations for Economic Impact Forecasts",
)
def explain_economic_impact_forecast(
    country: str = Query("USA", description="ISO3 country code"),
    horizon_days: int = Query(30, description="Forecast horizon in days (7, 30, 90)"),
    indicator: str = Query("inflation_impact_pct", description="Target economic indicator"),
    mode: str = Query("local", description="Explanation mode ('local' or 'global')"),
) -> Dict[str, Any]:
    """
    Generates exact SHAP values detailing feature contributions and rankings
    for macroeconomic transmission models.
    """
    return economic_service.get_explanation(
        country=country,
        horizon_days=horizon_days,
        target_indicator=indicator,
        mode=mode,
    )
