"""
Machine Learning Models Package for GeoIntelligence AI.

Includes:
- OilPriceForecaster: Single-horizon crude oil price forecasting (Brent & WTI)
- MultiHorizonOilForecaster: Multi-horizon (7d, 30d, 90d) pipeline orchestrator
- EconomicImpactForecaster: Mixed-frequency macroeconomic impact forecasting (7d, 30d, 90d)
- ModelComparisonResult, ForecastMetrics, EconomicImpactMetrics, EconomicModelComparisonResult
"""

from ml.models.oil_forecaster import (
    ForecastMetrics,
    ModelComparisonResult,
    MultiHorizonOilForecaster,
    OilPriceForecaster,
    SERIES_ALIASES,
    SUPPORTED_HORIZONS,
)
from ml.models.economic_impact import (
    EconomicImpactForecaster,
    EconomicImpactMetrics,
    EconomicModelComparisonResult,
    SUPPORTED_ECONOMIC_HORIZONS,
)

__all__ = [
    "OilPriceForecaster",
    "MultiHorizonOilForecaster",
    "ModelComparisonResult",
    "ForecastMetrics",
    "SUPPORTED_HORIZONS",
    "SERIES_ALIASES",
    "EconomicImpactForecaster",
    "EconomicImpactMetrics",
    "EconomicModelComparisonResult",
    "SUPPORTED_ECONOMIC_HORIZONS",
]
