"""
GeoIntelligence AI Data Pipeline Package.
Provides ingestion, standardization, and feature transformation for geopolitical forecasting.
"""

from src.data.config import (
    UCDP_SOURCE_NAME,
    UCDP_DATASET_NAME,
    UCDP_DATASET_VERSION,
    RAW_UCDP_DIR,
    PROCESSED_UCDP_DIR,
)

__all__ = [
    "UCDP_SOURCE_NAME",
    "UCDP_DATASET_NAME",
    "UCDP_DATASET_VERSION",
    "RAW_UCDP_DIR",
    "PROCESSED_UCDP_DIR",
]
