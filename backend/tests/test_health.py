"""Tests for Health and Info endpoints."""

from fastapi.testclient import TestClient


def test_root_health_endpoint(client: TestClient):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "annasetu-api"
    assert "version" in data


def test_api_v1_health_endpoint(client: TestClient):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "annasetu-api"


def test_api_v1_info_endpoint(client: TestClient):
    response = client.get("/api/v1/info")
    assert response.status_code == 200
    data = response.json()
    assert data["service"] == "annasetu-api"
    assert "DONOR" in data["roles_supported"]
    assert "RECEIVER" in data["roles_supported"]
    assert "DRIVER" in data["roles_supported"]
