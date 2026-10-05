from typing import Any, Dict
from fastapi import APIRouter, Body

from backend.schemas.scenarios import (
    ScenarioPresetsResponse,
    ScenarioSimulationRequest,
    ScenarioSimulationResponse,
)
from backend.services.scenario_service import scenario_service

router = APIRouter(prefix="/api/scenarios", tags=["What-If Scenarios"])


@router.get(
    "/presets",
    response_model=ScenarioPresetsResponse,
    summary="List Predefined Geopolitical and Energy Shock Scenarios",
)
def list_scenario_presets() -> Dict[str, Any]:
    """
    Returns available counterfactual scenario presets (e.g. positive oil shock,
    negative oil shock, supply chain crisis).
    """
    return {"presets": scenario_service.get_presets()}


@router.post(
    "/simulate",
    response_model=ScenarioSimulationResponse,
    summary="Simulate What-If Scenario through Trained ML Models",
)
def simulate_scenario(
    request: ScenarioSimulationRequest = Body(...),
) -> Dict[str, Any]:
    """
    Stress-tests forecasting models against custom or preset shock parameters,
    computing baseline vs scenario divergence and changed driver tracking.
    """
    return scenario_service.simulate(request)
