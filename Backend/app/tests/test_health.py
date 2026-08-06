"""Tests for the health check endpoint."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_returns_ok() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["service"] == "Purchase Order Automation API"
    assert payload["version"]
    assert payload["environment"] in {"development", "staging", "production"}


def test_health_reports_database_configuration_state() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    database = response.json()["database"]
    assert "configured" in database
    assert "detail" in database
