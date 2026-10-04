from dataclasses import dataclass
from typing import Dict, List, Optional, Union
import numpy as np
import pandas as pd


# Major maritime energy chokepoints recognized in international trade intelligence
CRITICAL_ENERGY_CHOKEPOINTS = {
    "STRAIT_OF_HORMUZ": {"region": "Middle East", "primary_commodity": "Crude Oil / LNG"},
    "BAB_EL_MANDEB": {"region": "Red Sea / Gulf of Aden", "primary_commodity": "Crude Oil / Refined / Container"},
    "SUEZ_CANAL": {"region": "Egypt / Mediterranean", "primary_commodity": "Container / Petroleum"},
    "MALACCA_STRAIT": {"region": "Southeast Asia", "primary_commodity": "Crude Oil / Dry Bulk"},
    "PANAMA_CANAL": {"region": "Central America", "primary_commodity": "LNG / LPG / Dry Bulk"},
    "TURKISH_STRAITS": {"region": "Black Sea / Mediterranean", "primary_commodity": "Crude Oil / Grain"},
}


def clean_trade_flow_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Cleans trade records (e.g. from UN Comtrade) for shipping feature extraction.
    """
    if df.empty:
        return pd.DataFrame(columns=[
            "period", "reporter_iso", "partner_iso", "commodity_code", "flow_code", "trade_value_usd", "net_weight_kg"
        ])

    cleaned = df.copy()

    # Normalize period to string year/date
    if "period" in cleaned.columns:
        cleaned["period"] = cleaned["period"].astype(str)

    # Convert numeric fields
    for num_col in ["trade_value_usd", "net_weight_kg"]:
        if num_col in cleaned.columns:
            cleaned[num_col] = pd.to_numeric(cleaned[num_col], errors="coerce").fillna(0.0)

    # Standardize country codes
    for iso_col in ["reporter_iso", "partner_iso"]:
        if iso_col in cleaned.columns:
            cleaned[iso_col] = cleaned[iso_col].astype(str).str.upper().str.strip()

    return cleaned


def extract_trade_concentration_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Calculates bilateral import/export partner concentration (Herfindahl-Hirschman Index - HHI)
    from observed UN Comtrade trade flows.

    High HHI values (closer to 1.0) signify heightened supply-chain vulnerability
    and single-corridor shipping risk.

    Anti-fabrication rule: Only computes metrics on real, observed trade flows.
    """
    cleaned = clean_trade_flow_data(df)
    if cleaned.empty:
        return pd.DataFrame(columns=[
            "period", "reporter_iso", "flow_code", "commodity_code", "total_trade_value_usd", "partner_count", "hhi_concentration"
        ])

    group_keys = [k for k in ["period", "reporter_iso", "flow_code", "commodity_code"] if k in cleaned.columns]
    if not group_keys or "trade_value_usd" not in cleaned.columns:
        return pd.DataFrame()

    results = []
    for keys, grp in cleaned.groupby(group_keys):
        total_val = grp["trade_value_usd"].sum()
        if total_val <= 0:
            hhi = 0.0
        else:
            shares = grp["trade_value_usd"] / total_val
            hhi = float((shares ** 2).sum())

        row = dict(zip(group_keys, keys if isinstance(keys, tuple) else [keys]))
        row["total_trade_value_usd"] = total_val
        row["partner_count"] = int((grp["trade_value_usd"] > 0).sum())
        row["hhi_concentration"] = round(hhi, 4)
        results.append(row)

    res_df = pd.DataFrame(results)
    return res_df.sort_values(by=group_keys).reset_index(drop=True)


@dataclass
class MaritimeChokepointObservation:
    """
    Schema for external maritime chokepoint transit observations (e.g. from AIS tracking).
    Designed to ingest real shipping metrics as external feeds become available.
    """
    chokepoint: str
    date: str
    transit_count: Optional[int] = None
    tanker_volume_barrels: Optional[float] = None
    average_wait_hours: Optional[float] = None
    freight_rate_index: Optional[float] = None
    incident_reported: Optional[bool] = None
    source: str = "External Maritime Tracking"


class ShippingRiskFeaturePipeline:
    """
    Feature-engineering interface for shipping and maritime supply chain risks.
    Combines verified commodity trade flows with external maritime tracking data.

    Design Principles:
    - Never fabricates shipping incidents, attacks, or synthetic transit numbers.
    - If external maritime telemetry is unavailable, flags data availability explicitly
      rather than returning hallucinated risk scores.
    """

    def __init__(self, chokepoint_registry: Optional[Dict[str, Dict[str, str]]] = None):
        self.chokepoints = chokepoint_registry or CRITICAL_ENERGY_CHOKEPOINTS

    def process_trade_shipping_exposure(self, trade_df: pd.DataFrame) -> pd.DataFrame:
        """
        Derives shipping exposure and partner concentration metrics from observed trade data.
        """
        return extract_trade_concentration_features(trade_df)

    def integrate_maritime_observations(
        self,
        observations: List[MaritimeChokepointObservation],
    ) -> pd.DataFrame:
        """
        Validates and converts external maritime tracking observations into a time-series panel.
        Rejects invalid observations without generating mock replacements.
        """
        if not observations:
            return pd.DataFrame(columns=[
                "chokepoint", "date", "transit_count", "tanker_volume_barrels",
                "average_wait_hours", "freight_rate_index", "incident_reported", "source"
            ])

        records = []
        for obs in observations:
            if not isinstance(obs, MaritimeChokepointObservation):
                continue
            if obs.chokepoint not in self.chokepoints:
                # Still record known or newly tracked maritime corridors
                pass

            records.append({
                "chokepoint": obs.chokepoint,
                "date": pd.to_datetime(obs.date, errors="coerce"),
                "transit_count": obs.transit_count,
                "tanker_volume_barrels": obs.tanker_volume_barrels,
                "average_wait_hours": obs.average_wait_hours,
                "freight_rate_index": obs.freight_rate_index,
                "incident_reported": obs.incident_reported,
                "source": obs.source,
            })

        df = pd.DataFrame(records).dropna(subset=["date"])
        return df.sort_values(by=["chokepoint", "date"]).reset_index(drop=True)
