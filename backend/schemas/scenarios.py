from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ScenarioSimulationRequest(BaseModel):
    target_type: str = Field(
        "oil",
        description="Target forecast domain ('oil' or 'economic')",
        pattern="^(oil|economic)$",
    )
    scenario_name: str = Field(
        "positive_oil_shock",
        description="Scenario preset ('baseline', 'positive_oil_shock', 'negative_oil_shock', 'supply_chain_crisis', 'custom')",
    )
    horizon_days: int = Field(30, description="Forecast horizon in days (7, 30, 90)")
    series: Optional[str] = Field("RBRTE", description="Oil series (RBRTE or RWTC) when target_type is 'oil'")
    country: Optional[str] = Field("USA", description="ISO3 country code when target_type is 'economic'")
    modifications: Optional[Dict[str, float]] = Field(
        default=None,
        description="Optional dictionary of custom feature perturbations (e.g. {'oil_price': 105.0, 'trade_hhi': 0.45})",
    )


class ChangedFeatureDetail(BaseModel):
    baseline: float
    scenario: float
    delta: float


class ScenarioSimulationResponse(BaseModel):
    scenario_name: str
    target_type: str
    horizon_days: int
    baseline_forecast: float
    scenario_forecast: float
    absolute_difference: float
    percentage_difference: float
    changed_inputs: Optional[Dict[str, Any]] = Field(None, description="Direct summary of changed inputs for frontend display")
    changed_input_features: Dict[str, ChangedFeatureDetail]
    as_of_date: str
    forecast_target_date: str
    limitations_notice: Optional[str] = Field(
        "Counterfactual scenario outputs represent model projections under hypothetical input shocks and should not be interpreted as guaranteed outcomes.",
        description="Important model caveats for frontend display",
    )


class ScenarioPresetsResponse(BaseModel):
    presets: Dict[str, str]
