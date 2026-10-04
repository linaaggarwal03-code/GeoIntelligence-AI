import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import pandas as pd

from backend.config import settings
from ml.data_ingestion.http_client import (
    APIResponseError,
    HTTPClient,
    logger,
    save_raw_json,
)


class ComtradeFetcher:
    """
    Client for UN Comtrade API (v1).
    Fetches international trade statistics (imports, exports, crude petroleum flows).

    PUBLIC ENDPOINT LIMITATIONS & SUBSCRIPTION KEYS:
    - UN Comtrade API v1 uses Azure API Management (comtradeapi.un.org).
    - When no API key is provided, the fetcher calls the public preview endpoint
      (https://comtradeapi.un.org/public/v1/preview/C/A/HS), which is subject to
      strict public throttling and a maximum of 500 records per request.
    - For high-volume or production queries, configure COMTRADE_API_KEY in the environment
      or .env file (obtained from https://comtradeplus.un.org/). The fetcher will then
      route requests to the authenticated endpoint (https://comtradeapi.un.org/data/v1/get/C/A/HS)
      with the 'Ocp-Apim-Subscription-Key' header.
    """

    PREVIEW_BASE_URL = "https://comtradeapi.un.org/public/v1/preview/C/A/HS"
    AUTHENTICATED_BASE_URL = "https://comtradeapi.un.org/data/v1/get/C/A/HS"

    # Common energy and commodity codes for quick reference
    CRUDE_PETROLEUM_HS = "2709"  # Petroleum oils and oils obtained from bituminous minerals; crude
    MINERAL_FUELS_HS = "27"      # Mineral fuels, mineral oils and products of their distillation

    def __init__(
        self,
        api_key: Optional[str] = None,
        use_preview: Optional[bool] = None,
        http_client: Optional[HTTPClient] = None,
        raw_data_dir: Union[str, Path] = Path("data/raw/comtrade"),
    ):
        self.api_key = api_key or settings.COMTRADE_API_KEY or os.getenv("COMTRADE_API_KEY")
        # If explicitly told to use preview or if no key is present, default to public preview
        if use_preview is not None:
            self.use_preview = use_preview
        else:
            self.use_preview = not bool(self.api_key)

        self.http_client = http_client or HTTPClient()
        self.raw_data_dir = Path(raw_data_dir)

    def fetch_trade_data(
        self,
        period: Union[int, str],
        reporter_code: Union[int, str] = "0",
        partner_code: Union[int, str] = "0",
        cmd_code: str = CRUDE_PETROLEUM_HS,
        flow_code: Optional[str] = None,
        save_raw: bool = True,
    ) -> pd.DataFrame:
        """
        Fetch trade flow records for a given commodity, period, and reporting country.

        :param period: Year (e.g. 2022, 2023, '2023')
        :param reporter_code: ISO 3-digit numeric code for reporting country (e.g. 842 for USA, 0 for World)
        :param partner_code: ISO 3-digit numeric code for partner country (e.g. 0 for World)
        :param cmd_code: Harmonized System (HS) commodity code (default '2709' for crude petroleum)
        :param flow_code: Trade flow ('M' = Imports, 'X' = Exports, 'RX' = Re-exports, None = All)
        :param save_raw: Whether to save raw JSON response
        :return: Structured pandas DataFrame
        """
        params: Dict[str, Any] = {
            "period": str(period),
            "reporterCode": str(reporter_code),
            "partnerCode": str(partner_code),
            "cmdCode": str(cmd_code),
        }
        if flow_code:
            params["flowCode"] = str(flow_code)

        headers: Dict[str, str] = {}
        if not self.use_preview and self.api_key:
            url = self.AUTHENTICATED_BASE_URL
            headers["Ocp-Apim-Subscription-Key"] = self.api_key
        else:
            url = self.PREVIEW_BASE_URL
            if self.api_key:
                headers["Ocp-Apim-Subscription-Key"] = self.api_key

        try:
            payload = self.http_client.get_json(url, params=params, headers=headers)
        except APIResponseError as e:
            if e.status_code in (401, 403):
                raise APIResponseError(
                    f"UN Comtrade authentication failed (HTTP {e.status_code}). "
                    "Ensure COMTRADE_API_KEY is a valid subscription key from https://comtradeplus.un.org/, "
                    "or instantiate ComtradeFetcher(use_preview=True) for limited public preview.",
                    status_code=e.status_code,
                    response_text=e.response_text,
                ) from e
            elif e.status_code == 429:
                raise APIResponseError(
                    "UN Comtrade rate limit exceeded (HTTP 429). The public endpoint permits limited requests per minute.",
                    status_code=e.status_code,
                    response_text=e.response_text,
                ) from e
            raise

        records = self._validate_response(payload, period=period, cmd_code=cmd_code)

        if save_raw:
            flow_tag = f"_{flow_code}" if flow_code else ""
            filename = f"comtrade_{reporter_code}_{partner_code}_{cmd_code}_{period}{flow_tag}.json"
            save_raw_json(payload, self.raw_data_dir / filename)

        return self._to_dataframe(records)

    def _validate_response(self, payload: Any, period: Union[int, str], cmd_code: str) -> List[Dict[str, Any]]:
        """
        Validates UN Comtrade API response payload.
        """
        if not isinstance(payload, dict):
            raise APIResponseError(f"Unexpected Comtrade response format: expected dict, got {type(payload)}")

        if payload.get("statusCode") and payload.get("statusCode") != 200:
            msg = payload.get("message", "Unknown Comtrade API error")
            raise APIResponseError(f"UN Comtrade API error: {msg}", status_code=payload.get("statusCode"))

        if "error" in payload and payload["error"]:
            raise APIResponseError(f"UN Comtrade API reported error: {payload['error']}")

        data = payload.get("data")
        if data is None:
            raise APIResponseError(
                f"Malformed UN Comtrade response for period={period}, cmdCode={cmd_code}: missing 'data' list"
            )

        if not isinstance(data, list):
            raise APIResponseError(f"UN Comtrade 'data' is not a list: got {type(data)}")

        return data

    def _to_dataframe(self, records: List[Dict[str, Any]]) -> pd.DataFrame:
        """
        Converts Comtrade records into a clean, standardized DataFrame.
        """
        columns = [
            "period",
            "reporter_iso",
            "reporter_desc",
            "partner_iso",
            "partner_desc",
            "commodity_code",
            "commodity_desc",
            "flow_code",
            "flow_desc",
            "trade_value_usd",
            "net_weight_kg",
            "source",
        ]

        if not records:
            logger.warning("No trade records returned by UN Comtrade query.")
            return pd.DataFrame(columns=columns)

        flattened = []
        for r in records:
            if not isinstance(r, dict):
                continue
            flattened.append({
                "period": str(r.get("period", "")),
                "reporter_iso": r.get("reporterISO"),
                "reporter_desc": r.get("reporterDesc"),
                "partner_iso": r.get("partnerISO"),
                "partner_desc": r.get("partnerDesc"),
                "commodity_code": str(r.get("cmdCode", "")),
                "commodity_desc": r.get("cmdDesc"),
                "flow_code": r.get("flowCode"),
                "flow_desc": r.get("flowDesc"),
                "trade_value_usd": r.get("primaryValue"),
                "net_weight_kg": r.get("netWgt"),
                "source": "UN Comtrade API v1",
            })

        df = pd.DataFrame(flattened)

        if "trade_value_usd" in df.columns:
            df["trade_value_usd"] = pd.to_numeric(df["trade_value_usd"], errors="coerce")

        if "net_weight_kg" in df.columns:
            df["net_weight_kg"] = pd.to_numeric(df["net_weight_kg"], errors="coerce")

        # Deduplicate records by period, reporter, partner, commodity, and flow
        dedup_keys = [k for k in ["period", "reporter_iso", "partner_iso", "commodity_code", "flow_code"] if k in df.columns]
        if dedup_keys:
            df = df.drop_duplicates(subset=dedup_keys, keep="last")

        return df.reset_index(drop=True)
