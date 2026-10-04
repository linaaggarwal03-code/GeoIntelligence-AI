import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import pandas as pd

from backend.config import settings
from ml.data_ingestion.http_client import (
    APIKeyMissingError,
    APIResponseError,
    HTTPClient,
    logger,
    save_raw_json,
)


class EIAFetcher:
    """
    Client for the U.S. Energy Information Administration (EIA) v2 API.
    Retrieves time-series data for crude oil prices, production, and energy indicators.
    """

    DEFAULT_BASE_URL = "https://api.eia.gov/v2/"

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: str = DEFAULT_BASE_URL,
        http_client: Optional[HTTPClient] = None,
        raw_data_dir: Union[str, Path] = Path("data/raw/eia"),
    ):
        # Resolve API key from argument, backend settings, or environment
        self.api_key = api_key or settings.EIA_API_KEY or os.getenv("EIA_API_KEY")
        self.base_url = base_url.rstrip("/") + "/"
        self.http_client = http_client or HTTPClient()
        self.raw_data_dir = Path(raw_data_dir)

    def _ensure_api_key(self) -> str:
        if not self.api_key:
            raise APIKeyMissingError(
                "EIA_API_KEY is not configured. Please supply it via environment variable, "
                ".env file, or the constructor. Obtain a free key at https://www.eia.gov/opendata/"
            )
        return self.api_key

    def fetch_series(
        self,
        route: str,
        series_id: Optional[str] = None,
        frequency: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        data_field: str = "value",
        length: int = 5000,
        save_raw: bool = True,
    ) -> pd.DataFrame:
        """
        Fetch time-series data from an EIA v2 endpoint.

        :param route: API route relative to base_url, e.g. 'petroleum/pri/spt/data/'
        :param series_id: Specific series identifier (e.g. 'RBRTE' for Brent, 'RWTC' for WTI)
        :param frequency: Data frequency ('daily', 'weekly', 'monthly', 'annual')
        :param start_date: Start date string (e.g. '2020-01-01')
        :param end_date: End date string (e.g. '2026-12-31')
        :param data_field: Field name to fetch (default 'value')
        :param length: Maximum records to return
        :param save_raw: Whether to save raw JSON payload to disk
        :return: Cleaned and structured pandas DataFrame
        """
        api_key = self._ensure_api_key()
        clean_route = route.strip("/") + "/"
        url = f"{self.base_url}{clean_route}"

        params: Dict[str, Any] = {
            "api_key": api_key,
            "data[0]": data_field,
            "sort[0][column]": "period",
            "sort[0][direction]": "asc",
            "length": length,
        }
        if frequency:
            params["frequency"] = frequency
        if series_id:
            params["facets[series][]"] = series_id
        if start_date:
            params["start"] = start_date
        if end_date:
            params["end"] = end_date

        payload = self.http_client.get_json(url, params=params)
        validated_data = self._validate_response(payload, route=route)

        if save_raw:
            slug = route.replace("/", "_").strip("_")
            series_tag = f"_{series_id}" if series_id else ""
            freq_tag = f"_{frequency}" if frequency else ""
            filename = f"{slug}{series_tag}{freq_tag}.json"
            save_raw_json(payload, self.raw_data_dir / filename)

        return self._to_dataframe(validated_data, source_route=route)

    def _validate_response(self, payload: Any, route: str) -> List[Dict[str, Any]]:
        """
        Validates EIA v2 API response structure and reports API-side errors.
        """
        if not isinstance(payload, dict):
            raise APIResponseError(f"Unexpected response format from EIA route '{route}': expected dict, got {type(payload)}")

        if "error" in payload:
            err = payload["error"]
            msg = err.get("message", str(err)) if isinstance(err, dict) else str(err)
            raise APIResponseError(f"EIA API error on route '{route}': {msg}")

        if "response" not in payload:
            raise APIResponseError(f"Malformed EIA API response: missing 'response' key on route '{route}'")

        response_body = payload["response"]
        if not isinstance(response_body, dict) or "data" not in response_body:
            raise APIResponseError(f"Malformed EIA API response: missing 'data' field in 'response' on route '{route}'")

        data = response_body["data"]
        if not isinstance(data, list):
            raise APIResponseError(f"Malformed EIA API response: 'data' is not a list on route '{route}'")

        return data

    def _to_dataframe(self, data: List[Dict[str, Any]], source_route: str) -> pd.DataFrame:
        """
        Converts raw EIA record list into a validated, sorted, deduplicated DataFrame.
        """
        if not data:
            logger.warning(f"No records returned by EIA for route '{source_route}'")
            return pd.DataFrame(columns=["period", "series", "value", "units", "series_description", "source"])

        df = pd.DataFrame(data)

        # Standardize standard EIA column names
        rename_map = {
            "series-description": "series_description",
        }
        df = df.rename(columns=rename_map)

        if "period" in df.columns:
            df["period"] = pd.to_datetime(df["period"], errors="coerce")
            df = df.dropna(subset=["period"])
            df = df.sort_values(by="period")

        if "value" in df.columns:
            df["value"] = pd.to_numeric(df["value"], errors="coerce")

        if "series" in df.columns and "period" in df.columns:
            df = df.drop_duplicates(subset=["period", "series"], keep="last")

        df["source"] = f"EIA:{source_route}"
        return df.reset_index(drop=True)

    def fetch_oil_spot_prices(
        self,
        series: str = "RBRTE",
        frequency: str = "daily",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        save_raw: bool = True,
    ) -> pd.DataFrame:
        """
        Convenience method to fetch Crude Oil Spot Prices (e.g. RBRTE = Brent, RWTC = WTI).
        """
        return self.fetch_series(
            route="petroleum/pri/spt/data/",
            series_id=series,
            frequency=frequency,
            start_date=start_date,
            end_date=end_date,
            save_raw=save_raw,
        )
