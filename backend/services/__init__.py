"""
Service Layer for GeoIntelligence AI (Economic & Oil Forecasting Module).
"""

from backend.services.economic_service import EconomicService, economic_service
from backend.services.oil_service import OilService, oil_service
from backend.services.scenario_service import ScenarioService, scenario_service
from backend.services.shipping_service import ShippingService, shipping_service

__all__ = [
    "OilService",
    "oil_service",
    "EconomicService",
    "economic_service",
    "ShippingService",
    "shipping_service",
    "ScenarioService",
    "scenario_service",
]
