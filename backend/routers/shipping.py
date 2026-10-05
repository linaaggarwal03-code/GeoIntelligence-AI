from typing import Any, Dict
from fastapi import APIRouter, Query

from backend.schemas.shipping import ChokepointsResponse, TradeConcentrationResponse
from backend.services.shipping_service import shipping_service

router = APIRouter(prefix="/api/shipping", tags=["Shipping & Trade Risk"])


@router.get(
    "/chokepoints",
    response_model=ChokepointsResponse,
    summary="Get Critical Maritime Energy Chokepoints Registry",
)
def get_maritime_chokepoints() -> Dict[str, Any]:
    """
    Returns the monitored strategic maritime corridors (e.g. Hormuz, Bab el-Mandeb,
    Suez, Malacca, Panama) and primary commodity types.
    """
    return shipping_service.get_chokepoints()


@router.get(
    "/trade-concentration",
    response_model=TradeConcentrationResponse,
    summary="Get Bilateral Trade Concentration & Supply-Chain Risk (HHI)",
)
def get_trade_concentration_metrics(
    period: str = Query("2022", description="Trade reporting year (e.g. '2022')"),
    reporter_code: str = Query("842", description="ISO numeric country code (e.g. '842' for USA)"),
    partner_code: str = Query("0", description="ISO numeric partner code ('0' for World)"),
    cmd_code: str = Query("2709", description="Harmonized System commodity code ('2709' for crude petroleum)"),
) -> Dict[str, Any]:
    """
    Computes partner concentration metrics (Herfindahl-Hirschman Index - HHI)
    from observed UN Comtrade bilateral trade flows to evaluate supply-chain vulnerability.
    """
    records = shipping_service.get_trade_concentration(
        period=period,
        reporter_code=reporter_code,
        partner_code=partner_code,
        cmd_code=cmd_code,
    )
    return {
        "status": "success",
        "count": len(records),
        "data": records,
    }
