from pathlib import Path
from typing import Any, Dict, List, Optional
from fastapi import HTTPException
import pandas as pd

from ml.data_ingestion.comtrade_fetcher import ComtradeFetcher
from ml.data_ingestion.http_client import APIResponseError
from ml.features.shipping_features import (
    CRITICAL_ENERGY_CHOKEPOINTS,
    extract_trade_concentration_features,
)


class ShippingService:
    """
    Service layer providing maritime chokepoint intelligence and bilateral trade concentration metrics.
    """

    def __init__(self, raw_data_dir: Path = Path("data/raw/comtrade")):
        self.raw_data_dir = raw_data_dir
        self.fetcher = ComtradeFetcher(raw_data_dir=raw_data_dir)
        self._trade_cache: Dict[str, pd.DataFrame] = {}

    def get_chokepoints(self) -> Dict[str, Any]:
        """Returns the registered energy and maritime chokepoint corridors."""
        return {
            "monitored_corridors_count": len(CRITICAL_ENERGY_CHOKEPOINTS),
            "chokepoints": CRITICAL_ENERGY_CHOKEPOINTS,
        }

    def set_in_memory_data(self, key: str, df: pd.DataFrame) -> None:
        """Inject test or offline datasets directly into service."""
        self._trade_cache[key] = df

    def get_trade_concentration(
        self,
        period: str = "2022",
        reporter_code: str = "842",
        partner_code: str = "0",
        cmd_code: str = "2709",
    ) -> List[Dict[str, Any]]:
        """
        Retrieves bilateral trade flows and calculates Herfindahl-Hirschman Index (HHI) concentration.
        """
        cache_key = f"{reporter_code}_{partner_code}_{cmd_code}_{period}"

        if cache_key in self._trade_cache:
            raw_trade = self._trade_cache[cache_key]
        else:
            try:
                raw_trade = self.fetcher.fetch_trade_data(
                    period=period,
                    reporter_code=reporter_code,
                    partner_code=partner_code,
                    cmd_code=cmd_code,
                )
                self._trade_cache[cache_key] = raw_trade
            except APIResponseError as e:
                raise HTTPException(
                    status_code=502,
                    detail=f"UN Comtrade API error: {str(e)}",
                )

        if raw_trade.empty:
            return []

        hhi_df = extract_trade_concentration_features(raw_trade)
        if hhi_df.empty:
            return []

        results = []
        for _, row in hhi_df.iterrows():
            hhi = float(row.get("hhi_concentration", 0.0))

            if hhi < 0.15:
                vuln = "Low"
            elif hhi < 0.25:
                vuln = "Moderate"
            elif hhi < 0.50:
                vuln = "High"
            else:
                vuln = "Critical"

            results.append({
                "period": str(row.get("period", period)),
                "reporter_iso": row.get("reporter_iso"),
                "commodity_code": str(row.get("commodity_code", cmd_code)),
                "partner_count": int(row.get("partner_count", 1)),
                "hhi_concentration": round(hhi, 4),
                "total_trade_value_usd": round(float(row.get("total_trade_value_usd", 0.0)), 2),
                "vulnerability_level": vuln,
            })

        return results


shipping_service = ShippingService()
