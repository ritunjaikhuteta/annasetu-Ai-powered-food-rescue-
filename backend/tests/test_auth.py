"""Tests for Authentication dependencies and /api/v1/me."""

from fastapi.testclient import TestClient


def test_unauthorized_access_missing_token(client: TestClient):
    response = client.get("/api/v1/me")
    assert response.status_code == 401
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "UNAUTHORIZED"


def test_unauthorized_access_invalid_token(client: TestClient):
    response = client.get(
        "/api/v1/me",
        headers={"Authorization": "Bearer invalid-or-forged-token"},
    )
    assert response.status_code == 401
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "UNAUTHORIZED"


def test_authenticated_me_donor_verified(client: TestClient):
    response = client.get(
        "/api/v1/me",
        headers={"Authorization": "Bearer token-user-donor-verified"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["user"]["id"] == "user-donor-verified"
    assert data["role"] == "DONOR"
    assert data["profile"]["role"] == "DONOR"
    assert data["verification_status"] == "VERIFIED"
    assert data["is_verified"] is True


def test_authenticated_me_donor_pending(client: TestClient):
    response = client.get(
        "/api/v1/me",
        headers={"Authorization": "Bearer token-user-donor-pending"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["user"]["id"] == "user-donor-pending"
    assert data["role"] == "DONOR"
    assert data["verification_status"] == "PENDING"
    assert data["is_verified"] is False
