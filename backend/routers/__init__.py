"""
FastAPI Routers for GeoIntelligence AI (Economic & Oil Forecasting Module).
"""

from backend.routers.economic import router as economic_router
from backend.routers.oil import router as oil_router
from backend.routers.scenarios import router as scenarios_router
from backend.routers.shipping import router as shipping_router

__all__ = [
    "oil_router",
    "economic_router",
    "shipping_router",
    "scenarios_router",
]
