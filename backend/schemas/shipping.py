from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ChokepointInfo(BaseModel):
    region: str
    primary_commodity: str


class ChokepointsResponse(BaseModel):
    monitored_corridors_count: int
    chokepoints: Dict[str, ChokepointInfo]


class TradeConcentrationItem(BaseModel):
    period: str
    reporter_iso: Optional[str] = None
    commodity_code: Optional[str] = None
    partner_count: int
    hhi_concentration: float = Field(..., description="Herfindahl-Hirschman Index between 0.0 and 1.0")
    total_trade_value_usd: float
    vulnerability_level: str = Field(..., description="Low, Moderate, High, or Critical")


class TradeConcentrationResponse(BaseModel):
    status: str
    count: int
    data: List[TradeConcentrationItem]
