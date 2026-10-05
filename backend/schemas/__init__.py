"""
Pydantic API Schemas for GeoIntelligence AI (Economic & Oil Forecasting Module).
"""

from backend.schemas.oil import (
    OilEvaluationMetrics,
    OilEvaluationResponse,
    OilExplanationResponse,
    OilForecastResponse,
)
from backend.schemas.economic import (
    EconomicEvaluationMetrics,
    EconomicEvaluationResponse,
    EconomicExplanationResponse,
    EconomicForecastResponse,
)
from backend.schemas.shipping import (
    ChokepointInfo,
    ChokepointsResponse,
    TradeConcentrationItem,
    TradeConcentrationResponse,
)
from backend.schemas.scenarios import (
    ChangedFeatureDetail,
    ScenarioPresetsResponse,
    ScenarioSimulationRequest,
    ScenarioSimulationResponse,
)

__all__ = [
    "OilForecastResponse",
    "OilEvaluationMetrics",
    "OilEvaluationResponse",
    "OilExplanationResponse",
    "EconomicForecastResponse",
    "EconomicEvaluationMetrics",
    "EconomicEvaluationResponse",
    "EconomicExplanationResponse",
    "ChokepointInfo",
    "ChokepointsResponse",
    "TradeConcentrationItem",
    "TradeConcentrationResponse",
    "ScenarioSimulationRequest",
    "ChangedFeatureDetail",
    "ScenarioSimulationResponse",
    "ScenarioPresetsResponse",
]
