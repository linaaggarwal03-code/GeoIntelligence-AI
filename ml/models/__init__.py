"""
Machine Learning Models Package for GeoIntelligence AI.

Includes:
- OilPriceForecaster: Single-horizon crude oil price forecasting (Brent & WTI)
- MultiHorizonOilForecaster: Multi-horizon (7d, 30d, 90d) pipeline orchestrator
- ModelComparisonResult, ForecastMetrics: Evaluation and benchmarking structures
"""

from ml.models.oil_forecaster import (
    ForecastMetrics,
    ModelComparisonResult,
    MultiHorizonOilForecaster,
    OilPriceForecaster,
    SERIES_ALIASES,
    SUPPORTED_HORIZONS,
)

__all__ = [
    "OilPriceForecaster",
    "MultiHorizonOilForecaster",
    "ModelComparisonResult",
    "ForecastMetrics",
    "SUPPORTED_HORIZONS",
    "SERIES_ALIASES",
]
