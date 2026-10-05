import json
import os
import pytest
from fastapi.testclient import TestClient

from backend.config import settings
from backend.main import app
from backend.schemas.oil import OilForecastResponse, OilEvaluationResponse, OilExplanationResponse
from backend.schemas.economic import EconomicForecastResponse, EconomicEvaluationResponse, EconomicExplanationResponse
from backend.schemas.shipping import ChokepointsResponse, TradeConcentrationResponse
from backend.schemas.scenarios import ScenarioSimulationResponse, ScenarioPresetsResponse
from ml.data_ingestion.eia_fetcher import EIAFetcher
from ml.data_ingestion.worldbank_fetcher import WorldBankFetcher
from ml.data_ingestion.comtrade_fetcher import ComtradeFetcher
from ml.data_ingestion.http_client import APIKeyMissingError, APIResponseError
from ml.features.economic_features import build_economic_panel, clean_worldbank_data
from ml.features.shipping_features import extract_trade_concentration_features


client = TestClient(app)


# ---------------------------------------------------------------------------
# 1. Live Data Smoke Tests (Public APIs & Conditional EIA)
# ---------------------------------------------------------------------------

def test_live_worldbank_smoke():
    """
    Live smoke test against public World Bank API.
    Must fetch genuine observations, parse them, and build an economic panel.
    """
    fetcher = WorldBankFetcher()
    try:
        df = fetcher.fetch_indicator(
            indicator="NY.GDP.MKTP.CD",
            country="USA",
            start_year=2022,
            end_year=2023,
            per_page=5,
            save_raw=False,
        )
    except Exception as e:
        pytest.fail(f"Live World Bank request failed unexpectedly: {e}")

    assert not df.empty, "World Bank should return records for USA GDP"
    assert "country_iso3" in df.columns
    assert "year" in df.columns
    assert "value" in df.columns
    assert df["country_iso3"].iloc[0] == "USA"
    assert df["value"].iloc[0] > 1e12

    # Verify downstream feature integration with live data
    panel = build_economic_panel(df, impute_strategy="none")
    assert not panel.empty
    assert "year" in panel.columns


def test_live_comtrade_preview_smoke():
    """
    Live smoke test against UN Comtrade public preview endpoint.
    Must fetch genuine crude petroleum import flow for USA in 2022.
    """
    fetcher = ComtradeFetcher(use_preview=True)
    try:
        df = fetcher.fetch_trade_data(
            period=2022,
            reporter_code=842,  # USA
            partner_code=0,    # World
            cmd_code="2709",   # Crude petroleum
            flow_code="M",     # Imports
            save_raw=False,
        )
    except APIResponseError as e:
        if e.status_code in (401, 403, 429):
            pytest.skip(f"UN Comtrade public preview throttled or restricted (HTTP {e.status_code}): {e}")
        else:
            pytest.fail(f"Live UN Comtrade request failed: {e}")

    assert not df.empty, "UN Comtrade should return observed trade record"
    assert "trade_value_usd" in df.columns
    assert df["trade_value_usd"].iloc[0] > 0

    # Verify downstream concentration calculation
    hhi_df = extract_trade_concentration_features(df)
    assert not hhi_df.empty
    assert "hhi_concentration" in hhi_df.columns


def test_live_eia_smoke():
    """
    Live smoke test for U.S. EIA API v2.
    Runs ONLY when EIA_API_KEY is configured; cleanly skips otherwise.
    """
    api_key = settings.EIA_API_KEY or os.getenv("EIA_API_KEY")
    if not api_key:
        pytest.skip("EIA_API_KEY is not configured in environment or .env; skipping live EIA test.")

    fetcher = EIAFetcher(api_key=api_key)
    try:
        df = fetcher.fetch_oil_spot_prices(series="RBRTE", start_date="2024-01-01", end_date="2024-01-10", save_raw=False)
    except APIKeyMissingError:
        pytest.skip("EIA_API_KEY missing.")
    except APIResponseError as e:
        pytest.fail(f"Live EIA API call failed: {e}")

    assert not df.empty
    assert "value" in df.columns
    assert df["value"].iloc[0] > 0


# ---------------------------------------------------------------------------
# 2. End-to-End API Schema Consistency and JSON Serialization Verification
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def setup_controlled_test_data():
    """
    Supplies controlled in-memory data to services for API schema consistency tests.
    """
    import numpy as np
    import pandas as pd
    from backend.services.oil_service import oil_service
    from backend.services.economic_service import economic_service
    from backend.services.shipping_service import shipping_service

    np.random.seed(42)
    dates = pd.date_range("2023-01-01", periods=250, freq="B")
    prices = [75.0]
    for _ in range(249):
        prices.append(max(20.0, prices[-1] * (1.0 + np.random.normal(0.0002, 0.018))))

    brent_df = pd.DataFrame({"period": dates, "series": "RBRTE", "value": prices})
    wti_df = pd.DataFrame({"period": dates, "series": "RWTC", "value": prices})
    oil_service.set_in_memory_data("RBRTE", brent_df)
    oil_service.set_in_memory_data("RWTC", wti_df)

    macro_records = []
    for y in range(2015, 2024):
        macro_records.extend([
            {
                "country_iso3": "USA",
                "country_name": "United States",
                "indicator_id": "NY.GDP.MKTP.CD",
                "indicator_name": "GDP",
                "year": y,
                "value": 1.8e13 + (y - 2015) * 8e11,
                "source": "Mocked World Bank",
            },
            {
                "country_iso3": "USA",
                "country_name": "United States",
                "indicator_id": "FP.CPI.TOTL.ZG",
                "indicator_name": "Inflation",
                "year": y,
                "value": 2.1 + (y % 3) * 0.8,
                "source": "Mocked World Bank",
            },
            {
                "country_iso3": "USA",
                "country_name": "United States",
                "indicator_id": "NE.EXP.GNFS.ZS",
                "indicator_name": "Exports % GDP",
                "year": y,
                "value": 11.0,
                "source": "Mocked World Bank",
            },
            {
                "country_iso3": "USA",
                "country_name": "United States",
                "indicator_id": "NE.IMP.GNFS.ZS",
                "indicator_name": "Imports % GDP",
                "year": y,
                "value": 14.0,
                "source": "Mocked World Bank",
            },
        ])
    economic_service.set_in_memory_data("USA", pd.DataFrame(macro_records))

    trade_df = pd.DataFrame({
        "period": ["2022", "2022"],
        "reporter_iso": ["USA", "USA"],
        "partner_iso": ["CAN", "MEX"],
        "commodity_code": ["2709", "2709"],
        "flow_code": ["M", "M"],
        "trade_value_usd": [60000000.0, 40000000.0],
        "net_weight_kg": [300000.0, 200000.0],
    })
    shipping_service.set_in_memory_data("842_0_2709_2022", trade_df)

def test_api_schema_consistency_oil_endpoints():
    # 1. Forecast
    resp = client.get("/api/oil/forecast?series=brent&horizon_days=30")
    assert resp.status_code == 200
    json_data = resp.json()
    validated = OilForecastResponse.model_validate(json_data)
    assert validated.series == "RBRTE"
    assert validated.horizon_days == 30
    assert json.dumps(json_data)  # Pure JSON serialization

    # 2. Evaluation
    resp_eval = client.get("/api/oil/evaluate?series=wti&horizon_days=7")
    assert resp_eval.status_code == 200
    eval_json = resp_eval.json()
    validated_eval = OilEvaluationResponse.model_validate(eval_json)
    assert validated_eval.series == "RWTC"
    assert json.dumps(eval_json)

    # 3. Explanation
    resp_exp = client.get("/api/oil/explain?series=brent&horizon_days=30&mode=local")
    assert resp_exp.status_code == 200
    exp_json = resp_exp.json()
    validated_exp = OilExplanationResponse.model_validate(exp_json)
    assert validated_exp.mode == "local"
    assert json.dumps(exp_json)


def test_api_schema_consistency_economic_endpoints():
    # 1. Forecast
    resp = client.get("/api/economic/forecast?country=USA&horizon_days=30")
    assert resp.status_code == 200
    json_data = resp.json()
    validated = EconomicForecastResponse.model_validate(json_data)
    assert validated.country == "USA"
    assert json.dumps(json_data)

    # 2. Evaluation
    resp_eval = client.get("/api/economic/evaluate?country=USA&horizon_days=30")
    assert resp_eval.status_code == 200
    eval_json = resp_eval.json()
    validated_eval = EconomicEvaluationResponse.model_validate(eval_json)
    assert validated_eval.country == "USA"
    assert json.dumps(eval_json)

    # 3. Explanation
    resp_exp = client.get("/api/economic/explain?country=USA&horizon_days=30&mode=global")
    assert resp_exp.status_code == 200
    exp_json = resp_exp.json()
    validated_exp = EconomicExplanationResponse.model_validate(exp_json)
    assert validated_exp.mode == "global"
    assert json.dumps(exp_json)


def test_api_schema_consistency_shipping_endpoints():
    # 1. Chokepoints
    resp = client.get("/api/shipping/chokepoints")
    assert resp.status_code == 200
    data = resp.json()
    validated = ChokepointsResponse.model_validate(data)
    assert validated.monitored_corridors_count > 0
    assert json.dumps(data)

    # 2. Trade concentration
    resp_trade = client.get("/api/shipping/trade-concentration?period=2022&reporter_code=842")
    assert resp_trade.status_code == 200
    data_trade = resp_trade.json()
    validated_trade = TradeConcentrationResponse.model_validate(data_trade)
    assert validated_trade.status == "success"
    assert json.dumps(data_trade)


def test_api_schema_consistency_scenario_endpoints():
    # 1. Presets
    resp_pre = client.get("/api/scenarios/presets")
    assert resp_pre.status_code == 200
    data_pre = resp_pre.json()
    validated_pre = ScenarioPresetsResponse.model_validate(data_pre)
    assert "positive_oil_shock" in validated_pre.presets
    assert json.dumps(data_pre)

    # 2. Simulation
    payload = {
        "target_type": "oil",
        "scenario_name": "positive_oil_shock",
        "horizon_days": 30,
        "series": "brent",
    }
    resp_sim = client.post("/api/scenarios/simulate", json=payload)
    assert resp_sim.status_code == 200
    data_sim = resp_sim.json()
    validated_sim = ScenarioSimulationResponse.model_validate(data_sim)
    assert validated_sim.target_type == "oil_price"
    assert json.dumps(data_sim)
