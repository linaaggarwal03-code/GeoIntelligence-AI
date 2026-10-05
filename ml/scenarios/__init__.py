"""
What-If Scenario Simulation Package for GeoIntelligence AI (Economic & Oil Forecasting Module).

Includes:
- WhatIfEngine: Counterfactual simulation engine for energy shocks and macro transmission
- ScenarioResult: Standardized output structure for baseline vs scenario comparisons
- PRESET_SCENARIOS: Canonical scenario definitions
"""

from ml.scenarios.what_if_engine import (
    PRESET_SCENARIOS,
    ScenarioResult,
    WhatIfEngine,
)

__all__ = [
    "WhatIfEngine",
    "ScenarioResult",
    "PRESET_SCENARIOS",
]
