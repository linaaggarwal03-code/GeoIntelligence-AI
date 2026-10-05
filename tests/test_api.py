import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient

from backend.main import app
from backend.services.economic_service import economic_service
from backend.services.oil_service import oil_service
from backend.services.shipping_service import shipping_service


client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_mock_services():
    """
    Populates services with controlled in-memory data for unit testing
    so that tests never call external APIs.
    """
    # 1. Controlled Oil Dataset
    np.random.seed(42)
    dates = pd.date_range("2023-01-01", periods=250, freq="B")
    prices = [75.0]
    for _ in range(249):
        prices.append(max(20.0, prices[-1] * (1.0 + np.random.normal(0.0002, 0.018))))

    brent_df = pd.DataFrame({"period": dates, "series": "RBRTE", "value": prices})
    wti_df = pd.DataFrame({"period": dates, "series": "RWTC", "value": prices})
    oil_service.set_in_memory_data("RBRTE", brent_df)
    oil_service.set_in_memory_data("RWTC", wti_df)

    # 2. Controlled Macro Dataset
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

    # 3. Controlled Trade Flow Dataset
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


# ---------------------------------------------------------------------------
# Root and Health Tests
# ---------------------------------------------------------------------------

def test_api_root():
    resp = client.get("/")
    assert resp.status_code == 200
    assert resp.json()["status"] == "success"


def test_api_health():
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "healthy"


# ---------------------------------------------------------------------------
# Shipping Endpoints Tests
# ---------------------------------------------------------------------------

def test_shipping_chokepoints_endpoint():
    resp = client.get("/api/shipping/chokepoints")
    assert resp.status_code == 200
    data = resp.json()
    assert "chokepoints" in data
    assert data["monitored_corridors_count"] >= 5
    assert "STRAIT_OF_HORMUZ" in data["chokepoints"]


def test_shipping_trade_concentration_endpoint():
    resp = client.get("/api/shipping/trade-concentration?period=2022&reporter_code=842")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "success"
    assert data["count"] >= 1
    assert "hhi_concentration" in data["data"][0]
    assert data["data"][0]["vulnerability_level"] in ["Low", "Moderate", "High", "Critical"]


# ---------------------------------------------------------------------------
# Oil Forecasting Endpoints Tests
# ---------------------------------------------------------------------------

def test_oil_forecast_endpoint():
    resp = client.get("/api/oil/forecast?series=brent&horizon_days=30")
    assert resp.status_code == 200
    data = resp.json()
    assert data["series"] == "RBRTE"
    assert data["horizon_days"] == 30
    assert "predicted_price" in data
    assert "predicted_return_pct" in data
    assert data["predicted_price"] > 0


def test_oil_forecast_invalid_params():
    # Unsupported series
    resp = client.get("/api/oil/forecast?series=unsupported_oil")
    assert resp.status_code == 400

    # Unsupported horizon
    resp = client.get("/api/oil/forecast?series=brent&horizon_days=15")
    assert resp.status_code == 400


def test_oil_evaluation_endpoint():
    resp = client.get("/api/oil/evaluate?series=wti&horizon_days=7")
    assert resp.status_code == 200
    data = resp.json()
    assert data["series"] == "RWTC"
    assert "xgboost" in data
    assert "baseline_persistence" in data
    assert "mae" in data["xgboost"]


def test_oil_explanation_endpoint():
    # Local explanation
    resp_local = client.get("/api/oil/explain?series=brent&horizon_days=30&mode=local")
    assert resp_local.status_code == 200
    data_loc = resp_local.json()
    assert data_loc["mode"] == "local"
    assert "contributions" in data_loc["explanation"]

    # Global explanation
    resp_glob = client.get("/api/oil/explain?series=brent&horizon_days=30&mode=global")
    assert resp_glob.status_code == 200
    data_glob = resp_glob.json()
    assert data_glob["mode"] == "global"
    assert "feature_importances" in data_glob["explanation"]


# ---------------------------------------------------------------------------
# Economic Impact Endpoints Tests
# ---------------------------------------------------------------------------

def test_economic_forecast_endpoint():
    resp = client.get("/api/economic/forecast?country=USA&horizon_days=30")
    assert resp.status_code == 200
    data = resp.json()
    assert data["country"] == "USA"
    assert data["horizon_days"] == 30
    assert "predicted_impact_value" in data
    assert "baseline_reference_value" in data


def test_economic_evaluation_endpoint():
    resp = client.get("/api/economic/evaluate?country=USA&horizon_days=7")
    assert resp.status_code == 200
    data = resp.json()
    assert "ml_model" in data
    assert "baseline" in data


def test_economic_explanation_endpoint():
    resp = client.get("/api/economic/explain?country=USA&horizon_days=30&mode=local")
    assert resp.status_code == 200
    data = resp.json()
    assert "contributions" in data["explanation"]


# ---------------------------------------------------------------------------
# What-If Scenarios Endpoints Tests
# ---------------------------------------------------------------------------

def test_scenarios_presets_endpoint():
    resp = client.get("/api/scenarios/presets")
    assert resp.status_code == 200
    data = resp.json()
    assert "positive_oil_shock" in data["presets"]
    assert "negative_oil_shock" in data["presets"]


def test_scenarios_simulate_oil_endpoint():
    payload = {
        "target_type": "oil",
        "scenario_name": "positive_oil_shock",
        "horizon_days": 30,
        "series": "brent",
    }
    resp = client.post("/api/scenarios/simulate", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["scenario_name"] == "positive_oil_shock"
    assert data["target_type"] == "oil_price"
    assert data["horizon_days"] == 30
    assert data["scenario_forecast"] > 0
    assert "changed_input_features" in data


def test_scenarios_simulate_economic_endpoint():
    payload = {
        "target_type": "economic",
        "scenario_name": "positive_oil_shock",
        "horizon_days": 30,
        "country": "USA",
    }
    resp = client.post("/api/scenarios/simulate", json=payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["target_type"] == "economic_impact"
    assert "changed_input_features" in data


def test_scenarios_simulate_invalid_params():
    # Negative oil price
    payload = {
        "target_type": "oil",
        "scenario_name": "custom",
        "horizon_days": 30,
        "modifications": {"oil_price": -50.0},
    }
    resp = client.post("/api/scenarios/simulate", json=payload)
    assert resp.status_code == 400
