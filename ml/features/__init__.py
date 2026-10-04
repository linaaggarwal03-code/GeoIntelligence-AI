"""
Feature Engineering Layer for GeoIntelligence AI (Economic & Oil Forecasting Module).

Includes:
- Oil price time-series feature engineering (returns, volatility, lags, momentum, anti-leakage)
- Macroeconomic panel features (World Bank data cleaning, GDP growth, inflation, trade metrics)
- Maritime and shipping risk features (trade concentration HHI, chokepoint telemetry interface)
"""

from ml.features.oil_features import (
    build_oil_features,
    clean_oil_price_data,
    compute_rsi,
)
from ml.features.economic_features import (
    INDICATOR_RENAME_MAP,
    build_economic_panel,
    clean_worldbank_data,
    engineer_economic_features,
)
from ml.features.shipping_features import (
    CRITICAL_ENERGY_CHOKEPOINTS,
    MaritimeChokepointObservation,
    ShippingRiskFeaturePipeline,
    clean_trade_flow_data,
    extract_trade_concentration_features,
)

__all__ = [
    # Oil features
    "clean_oil_price_data",
    "compute_rsi",
    "build_oil_features",
    # Economic features
    "INDICATOR_RENAME_MAP",
    "clean_worldbank_data",
    "build_economic_panel",
    "engineer_economic_features",
    # Shipping features
    "CRITICAL_ENERGY_CHOKEPOINTS",
    "clean_trade_flow_data",
    "extract_trade_concentration_features",
    "MaritimeChokepointObservation",
    "ShippingRiskFeaturePipeline",
]
