import json
from pathlib import Path
from unittest.mock import MagicMock, patch
import pytest
import requests

from ml.data_ingestion.http_client import (
    APIKeyMissingError,
    APIResponseError,
    HTTPClient,
    save_raw_json,
)
from ml.data_ingestion.eia_fetcher import EIAFetcher
from ml.data_ingestion.worldbank_fetcher import WorldBankFetcher
from ml.data_ingestion.comtrade_fetcher import ComtradeFetcher


# ---------------------------------------------------------------------------
# HTTPClient Tests
# ---------------------------------------------------------------------------

def test_http_client_success():
    client = HTTPClient()
    mock_resp = MagicMock()
    mock_resp.ok = True
    mock_resp.status_code = 200
    mock_resp.json.return_value = {"status": "ok", "items": [1, 2, 3]}

    with patch.object(client.session, "get", return_value=mock_resp):
        data = client.get_json("https://api.example.com/data")
        assert data == {"status": "ok", "items": [1, 2, 3]}


def test_http_client_http_error():
    client = HTTPClient()
    mock_resp = MagicMock()
    mock_resp.ok = False
    mock_resp.status_code = 500
    mock_resp.text = "Internal Server Error"

    with patch.object(client.session, "get", return_value=mock_resp):
        with pytest.raises(APIResponseError) as exc_info:
            client.get_json("https://api.example.com/fail")
        assert exc_info.value.status_code == 500
        assert "500" in str(exc_info.value)


def test_http_client_timeout():
    client = HTTPClient()
    with patch.object(client.session, "get", side_effect=requests.exceptions.Timeout("Connection timed out")):
        with pytest.raises(APIResponseError) as exc_info:
            client.get("https://api.example.com/timeout")
        assert "timed out" in str(exc_info.value)


def test_http_client_malformed_json():
    client = HTTPClient()
    mock_resp = MagicMock()
    mock_resp.ok = True
    mock_resp.status_code = 200
    mock_resp.text = "<html>Not JSON</html>"
    mock_resp.json.side_effect = ValueError("Invalid JSON")

    with patch.object(client.session, "get", return_value=mock_resp):
        with pytest.raises(APIResponseError) as exc_info:
            client.get_json("https://api.example.com/bad-json")
        assert "Malformed JSON" in str(exc_info.value)


def test_save_raw_json(tmp_path):
    out_file = tmp_path / "sub" / "data.json"
    data = {"sample": "value", "count": 42}
    saved_path = save_raw_json(data, out_file)

    assert saved_path.exists()
    with open(saved_path, "r", encoding="utf-8") as f:
        loaded = json.load(f)
    assert loaded == data


# ---------------------------------------------------------------------------
# EIA Fetcher Tests
# ---------------------------------------------------------------------------

def test_eia_fetcher_missing_api_key(monkeypatch):
    # Ensure no API key in settings or env
    monkeypatch.setenv("EIA_API_KEY", "")
    with patch("backend.config.settings.EIA_API_KEY", None):
        fetcher = EIAFetcher(api_key=None)
        with pytest.raises(APIKeyMissingError) as exc_info:
            fetcher.fetch_series(route="petroleum/pri/spt/data/")
        assert "EIA_API_KEY is not configured" in str(exc_info.value)


def test_eia_fetcher_successful_parsing(tmp_path):
    mock_client = MagicMock()
    mock_client.get_json.return_value = {
        "response": {
            "total": 2,
            "data": [
                {
                    "period": "2024-01-02",
                    "series": "RBRTE",
                    "series-description": "Europe Brent Spot Price FOB",
                    "value": "77.50",
                    "units": "$/BBL",
                },
                {
                    "period": "2024-01-03",
                    "series": "RBRTE",
                    "series-description": "Europe Brent Spot Price FOB",
                    "value": "78.25",
                    "units": "$/BBL",
                },
            ],
        }
    }

    fetcher = EIAFetcher(api_key="test_key", http_client=mock_client, raw_data_dir=tmp_path)
    df = fetcher.fetch_oil_spot_prices(series="RBRTE")

    assert len(df) == 2
    assert "period" in df.columns
    assert "value" in df.columns
    assert "series" in df.columns
    assert df["value"].iloc[0] == 77.50
    assert df["value"].iloc[1] == 78.25
    assert df["series"].iloc[0] == "RBRTE"
    assert "EIA:" in df["source"].iloc[0]


def test_eia_fetcher_api_error_response(tmp_path):
    mock_client = MagicMock()
    mock_client.get_json.return_value = {
        "error": {
            "code": 403,
            "message": "User api_key is invalid",
        }
    }
    fetcher = EIAFetcher(api_key="invalid_key", http_client=mock_client, raw_data_dir=tmp_path)
    with pytest.raises(APIResponseError) as exc_info:
        fetcher.fetch_series(route="petroleum/pri/spt/data/")
    assert "invalid" in str(exc_info.value).lower()


def test_eia_fetcher_malformed_response(tmp_path):
    mock_client = MagicMock()
    mock_client.get_json.return_value = {"invalid_envelope": []}
    fetcher = EIAFetcher(api_key="test_key", http_client=mock_client, raw_data_dir=tmp_path)
    with pytest.raises(APIResponseError) as exc_info:
        fetcher.fetch_series(route="petroleum/pri/spt/data/")
    assert "missing 'response' key" in str(exc_info.value)


# ---------------------------------------------------------------------------
# World Bank Fetcher Tests
# ---------------------------------------------------------------------------

def test_worldbank_fetcher_single_page(tmp_path):
    mock_client = MagicMock()
    mock_client.get_json.return_value = [
        {"page": 1, "pages": 1, "per_page": 50, "total": 1},
        [
            {
                "indicator": {"id": "NY.GDP.MKTP.CD", "value": "GDP (current US$)"},
                "country": {"id": "USA", "value": "United States"},
                "countryiso3code": "USA",
                "date": "2023",
                "value": 27360000000000.0,
            }
        ],
    ]

    fetcher = WorldBankFetcher(http_client=mock_client, raw_data_dir=tmp_path)
    df = fetcher.fetch_indicator("NY.GDP.MKTP.CD", country="USA", start_year=2023, end_year=2023)

    assert len(df) == 1
    assert df["country_iso3"].iloc[0] == "USA"
    assert df["indicator_id"].iloc[0] == "NY.GDP.MKTP.CD"
    assert df["year"].iloc[0] == 2023
    assert df["value"].iloc[0] == 27360000000000.0


def test_worldbank_fetcher_pagination(tmp_path):
    mock_client = MagicMock()
    page1 = [
        {"page": 1, "pages": 2, "per_page": 1, "total": 2},
        [
            {
                "indicator": {"id": "NY.GDP.MKTP.KD.ZG", "value": "GDP growth"},
                "country": {"id": "IND", "value": "India"},
                "countryiso3code": "IND",
                "date": "2022",
                "value": 7.0,
            }
        ],
    ]
    page2 = [
        {"page": 2, "pages": 2, "per_page": 1, "total": 2},
        [
            {
                "indicator": {"id": "NY.GDP.MKTP.KD.ZG", "value": "GDP growth"},
                "country": {"id": "IND", "value": "India"},
                "countryiso3code": "IND",
                "date": "2023",
                "value": 7.5,
            }
        ],
    ]
    mock_client.get_json.side_effect = [page1, page2]

    fetcher = WorldBankFetcher(http_client=mock_client, raw_data_dir=tmp_path)
    df = fetcher.fetch_indicator("NY.GDP.MKTP.KD.ZG", country="IND")

    assert len(df) == 2
    assert mock_client.get_json.call_count == 2
    assert list(df["year"]) == [2022, 2023]


def test_worldbank_fetcher_api_error_response(tmp_path):
    mock_client = MagicMock()
    mock_client.get_json.return_value = [
        {"message": [{"id": "120", "value": "The provided parameter value is not valid"}]}
    ]

    fetcher = WorldBankFetcher(http_client=mock_client, raw_data_dir=tmp_path)
    with pytest.raises(APIResponseError) as exc_info:
        fetcher.fetch_indicator("INVALID.INDICATOR", country="USA")
    assert "not valid" in str(exc_info.value).lower()


# ---------------------------------------------------------------------------
# UN Comtrade Fetcher Tests
# ---------------------------------------------------------------------------

def test_comtrade_fetcher_success(tmp_path):
    mock_client = MagicMock()
    mock_client.get_json.return_value = {
        "elapsedTime": "0.1s",
        "count": 1,
        "data": [
            {
                "period": "2023",
                "reporterISO": "USA",
                "reporterDesc": "USA",
                "partnerISO": "SAU",
                "partnerDesc": "Saudi Arabia",
                "cmdCode": "2709",
                "cmdDesc": "Crude petroleum oils",
                "flowCode": "M",
                "flowDesc": "Imports",
                "primaryValue": 1500000000.0,
                "netWgt": 2500000.0,
            }
        ],
    }

    fetcher = ComtradeFetcher(http_client=mock_client, raw_data_dir=tmp_path)
    df = fetcher.fetch_trade_data(period=2023, reporter_code=842, partner_code=682, cmd_code="2709")

    assert len(df) == 1
    assert df["reporter_iso"].iloc[0] == "USA"
    assert df["partner_iso"].iloc[0] == "SAU"
    assert df["commodity_code"].iloc[0] == "2709"
    assert df["flow_code"].iloc[0] == "M"
    assert df["trade_value_usd"].iloc[0] == 1500000000.0
    assert df["net_weight_kg"].iloc[0] == 2500000.0


def test_comtrade_fetcher_auth_error_reporting(tmp_path):
    mock_client = MagicMock()
    mock_client.get_json.side_effect = APIResponseError(
        message="HTTP 401 received",
        status_code=401,
        response_text="Access denied due to invalid subscription key",
    )

    fetcher = ComtradeFetcher(api_key="bad_key", http_client=mock_client, raw_data_dir=tmp_path)
    with pytest.raises(APIResponseError) as exc_info:
        fetcher.fetch_trade_data(period=2023)
    assert "COMTRADE_API_KEY" in str(exc_info.value)
    assert "401" in str(exc_info.value)


def test_comtrade_fetcher_malformed_response(tmp_path):
    mock_client = MagicMock()
    mock_client.get_json.return_value = {"elapsedTime": "0.1s"}  # Missing 'data'

    fetcher = ComtradeFetcher(http_client=mock_client, raw_data_dir=tmp_path)
    with pytest.raises(APIResponseError) as exc_info:
        fetcher.fetch_trade_data(period=2023)
    assert "missing 'data' list" in str(exc_info.value)
