import pytest
from fastapi.testclient import TestClient
from backend.main import app
from backend.config import Settings, get_settings
from backend.database import get_db, SessionLocal, engine, Base


client = TestClient(app)


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {
        "message": "GeoIntelligence AI Backend is running",
        "status": "success",
    }


def test_health_check_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    assert response.json() == {
        "status": "healthy",
        "service": "GeoIntelligence AI",
    }


def test_settings_defaults():
    settings = get_settings()
    assert settings.APP_NAME == "GeoIntelligence AI"
    assert settings.APP_VERSION == "1.0.0"
    assert "sqlite" in settings.DATABASE_URL or "postgres" in settings.DATABASE_URL


def test_database_session():
    # Verify database session lifecycle
    db_gen = get_db()
    db = next(db_gen)
    assert db is not None
    # Finish generator to trigger cleanup
    try:
        next(db_gen)
    except StopIteration:
        pass
