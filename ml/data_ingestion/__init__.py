"""
Data Ingestion Layer for GeoIntelligence AI (Economic & Oil Forecasting Module).

Provides production fetchers for:
- EIA: U.S. Energy Information Administration oil & energy time series
- World Bank: Macroeconomic indicators (GDP, inflation, trade % of GDP, FDI)
- UN Comtrade: International trade and crude petroleum commodity flows
"""

from ml.data_ingestion.http_client import (
    APIKeyMissingError,
    APIResponseError,
    HTTPClient,
    IngestionError,
    save_raw_json,
)
from ml.data_ingestion.eia_fetcher import EIAFetcher
from ml.data_ingestion.worldbank_fetcher import DEFAULT_ECONOMIC_INDICATORS, WorldBankFetcher
from ml.data_ingestion.comtrade_fetcher import ComtradeFetcher

__all__ = [
    "HTTPClient",
    "IngestionError",
    "APIKeyMissingError",
    "APIResponseError",
    "save_raw_json",
    "EIAFetcher",
    "WorldBankFetcher",
    "DEFAULT_ECONOMIC_INDICATORS",
    "ComtradeFetcher",
]
