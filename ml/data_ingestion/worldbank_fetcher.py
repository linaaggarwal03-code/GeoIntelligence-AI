from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import pandas as pd

from ml.data_ingestion.http_client import (
    APIResponseError,
    HTTPClient,
    logger,
    save_raw_json,
)


# Priority indicators for geopolitical & economic forecasting
DEFAULT_ECONOMIC_INDICATORS = {
    "GDP_CURRENT_USD": "NY.GDP.MKTP.CD",
    "GDP_GROWTH_ANNUAL_PCT": "NY.GDP.MKTP.KD.ZG",
    "INFLATION_CONSUMER_PRICES_PCT": "FP.CPI.TOTL.ZG",
    "EXPORTS_PCT_GDP": "NE.EXP.GNFS.ZS",
    "IMPORTS_PCT_GDP": "NE.IMP.GNFS.ZS",
    "FDI_NET_INFLOWS_PCT_GDP": "BX.KLT.DINV.WD.GD.ZS",
}


class WorldBankFetcher:
    """
    Client for the public World Bank Open Data API (v2).
    Retrieves country-level macroeconomic indicators without requiring an API key.
    """

    DEFAULT_BASE_URL = "https://api.worldbank.org/v2"

    def __init__(
        self,
        base_url: str = DEFAULT_BASE_URL,
        http_client: Optional[HTTPClient] = None,
        raw_data_dir: Union[str, Path] = Path("data/raw/worldbank"),
    ):
        self.base_url = base_url.rstrip("/")
        self.http_client = http_client or HTTPClient()
        self.raw_data_dir = Path(raw_data_dir)

    def fetch_indicator(
        self,
        indicator: str,
        country: str = "all",
        start_year: Optional[int] = None,
        end_year: Optional[int] = None,
        per_page: int = 250,
        max_pages: int = 20,
        save_raw: bool = True,
    ) -> pd.DataFrame:
        """
        Fetch time-series observations for a specific World Bank indicator and country.

        :param indicator: World Bank indicator code (e.g. 'NY.GDP.MKTP.CD')
        :param country: ISO2, ISO3 country code, or 'all' (e.g. 'USA', 'IND', 'WLD')
        :param start_year: Optional start year (e.g. 2000)
        :param end_year: Optional end year (e.g. 2024)
        :param per_page: Number of observations per page (max 1000)
        :param max_pages: Maximum pagination loops to avoid runaway queries
        :param save_raw: Whether to save raw fetched payload to disk
        :return: Standardized pandas DataFrame
        """
        url = f"{self.base_url}/country/{country.lower()}/indicator/{indicator}"
        params: Dict[str, Any] = {
            "format": "json",
            "per_page": min(per_page, 1000),
            "page": 1,
        }

        date_range_str = None
        if start_year and end_year:
            date_range_str = f"{start_year}:{end_year}"
            params["date"] = date_range_str
        elif start_year:
            date_range_str = f"{start_year}:"
            params["date"] = date_range_str
        elif end_year:
            date_range_str = f":{end_year}"
            params["date"] = date_range_str

        all_records: List[Dict[str, Any]] = []
        raw_pages: List[Any] = []

        # Page 1
        page1_data = self.http_client.get_json(url, params=params)
        raw_pages.append(page1_data)
        meta, records = self._validate_response(page1_data, indicator=indicator, country=country)
        all_records.extend(records)

        total_pages = meta.get("pages", 1) if meta else 1
        current_page = 2

        # Handle remaining pages
        while current_page <= total_pages and current_page <= max_pages:
            params["page"] = current_page
            logger.info(f"Fetching World Bank page {current_page}/{total_pages} for {indicator} ({country})")
            page_data = self.http_client.get_json(url, params=params)
            raw_pages.append(page_data)
            _, page_records = self._validate_response(page_data, indicator=indicator, country=country)
            all_records.extend(page_records)
            current_page += 1

        if save_raw:
            date_tag = f"_{date_range_str.replace(':', '_')}" if date_range_str else ""
            filename = f"{country}_{indicator}{date_tag}.json"
            save_raw_json(raw_pages if len(raw_pages) > 1 else raw_pages[0], self.raw_data_dir / filename)

        return self._to_dataframe(all_records, indicator=indicator)

    def _validate_response(self, payload: Any, indicator: str, country: str) -> tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Validates World Bank two-element response format: [metadata, data_records].
        """
        if not isinstance(payload, list):
            raise APIResponseError(
                f"Unexpected World Bank response format for {indicator} ({country}): expected list, got {type(payload)}"
            )

        if len(payload) == 0:
            return {}, []

        # Check for World Bank error envelope: [{'message': [{'id': '120', 'value': ...}]}]
        if isinstance(payload[0], dict) and "message" in payload[0]:
            error_details = payload[0]["message"]
            msg = str(error_details)
            if isinstance(error_details, list) and len(error_details) > 0 and "value" in error_details[0]:
                msg = error_details[0]["value"]
            raise APIResponseError(f"World Bank API error for {indicator} ({country}): {msg}")

        if len(payload) < 2:
            raise APIResponseError(f"World Bank response truncated for {indicator} ({country}): missing records element")

        meta = payload[0] if isinstance(payload[0], dict) else {}
        records = payload[1]

        if records is None:
            records = []
        elif not isinstance(records, list):
            raise APIResponseError(
                f"Invalid records format from World Bank for {indicator} ({country}): expected list, got {type(records)}"
            )

        return meta, records

    def _to_dataframe(self, records: List[Dict[str, Any]], indicator: str) -> pd.DataFrame:
        """
        Extracts tabular features from nested World Bank indicator records.
        """
        if not records:
            logger.warning(f"No records found from World Bank for indicator '{indicator}'")
            return pd.DataFrame(columns=[
                "country_iso3", "country_name", "indicator_id", "indicator_name", "year", "value", "source"
            ])

        flattened = []
        for r in records:
            if not isinstance(r, dict):
                continue

            country_obj = r.get("country") or {}
            indicator_obj = r.get("indicator") or {}

            flattened.append({
                "country_iso3": r.get("countryiso3code") or country_obj.get("id"),
                "country_name": country_obj.get("value"),
                "indicator_id": indicator_obj.get("id") or indicator,
                "indicator_name": indicator_obj.get("value"),
                "year": r.get("date"),
                "value": r.get("value"),
                "source": "World Bank Open Data",
            })

        df = pd.DataFrame(flattened)

        if "year" in df.columns:
            df["year"] = pd.to_numeric(df["year"], errors="coerce")
            df = df.dropna(subset=["year"])
            df["year"] = df["year"].astype(int)

        if "value" in df.columns:
            df["value"] = pd.to_numeric(df["value"], errors="coerce")

        if "year" in df.columns and "country_iso3" in df.columns:
            df = df.sort_values(by=["country_iso3", "year"])
            df = df.drop_duplicates(subset=["country_iso3", "year", "indicator_id"], keep="last")

        return df.reset_index(drop=True)

    def fetch_multiple_indicators(
        self,
        indicators: List[str],
        countries: List[str],
        start_year: Optional[int] = None,
        end_year: Optional[int] = None,
    ) -> pd.DataFrame:
        """
        Fetches multiple indicators across multiple countries, concatenating into a tidy DataFrame.
        """
        dfs = []
        for country in countries:
            for ind in indicators:
                try:
                    df = self.fetch_indicator(
                        indicator=ind,
                        country=country,
                        start_year=start_year,
                        end_year=end_year,
                    )
                    if not df.empty:
                        dfs.append(df)
                except APIResponseError as e:
                    logger.warning(f"Skipping failed indicator fetch {ind} for {country}: {e}")

        if not dfs:
            return pd.DataFrame(columns=[
                "country_iso3", "country_name", "indicator_id", "indicator_name", "year", "value", "source"
            ])

        return pd.concat(dfs, ignore_index=True)
