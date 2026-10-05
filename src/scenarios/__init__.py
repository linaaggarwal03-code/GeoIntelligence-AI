"""
What-If Geopolitical Simulator Module for GeoIntelligence AI (Member 3 Milestone 4).
Provides deterministic counterfactual scenario shock simulation, relational network ripple propagation,
and counterfactual graph recalculation across the 125-country empirical network.
"""

from src.scenarios.config import (
    DEFAULT_DECAY_FACTOR,
    DEFAULT_PROPAGATION_DEPTH,
    SCENARIO_ARCHETYPES,
    OUTPUT_COUNTRY_IMPACTS_PATH,
    OUTPUT_DYAD_IMPACTS_PATH,
    OUTPUT_GRAPH_JSON_PATH,
    OUTPUT_SUMMARY_JSON_PATH,
)
from src.scenarios.engine import ScenarioEngine
from src.scenarios.schema import ScenarioDefinition, SimulationResult

__all__ = [
    "ScenarioEngine",
    "ScenarioDefinition",
    "SimulationResult",
    "SCENARIO_ARCHETYPES",
    "DEFAULT_PROPAGATION_DEPTH",
    "DEFAULT_DECAY_FACTOR",
    "OUTPUT_COUNTRY_IMPACTS_PATH",
    "OUTPUT_DYAD_IMPACTS_PATH",
    "OUTPUT_GRAPH_JSON_PATH",
    "OUTPUT_SUMMARY_JSON_PATH",
]
