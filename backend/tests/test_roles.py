"""Tests for Role Authorization and Cross-Role Barriers."""

from fastapi.testclient import TestClient


def test_donor_can_access_donor_profile(client: TestClient):
    response = client.get(
        "/api/v1/donor/profile",
        headers={"Authorization": "Bearer token-user-donor-verified"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["business_name"] == "Taj Catering"
    assert data["verification_status"] == "VERIFIED"


def test_receiver_cannot_access_donor_profile(client: TestClient):
    response = client.get(
        "/api/v1/donor/profile",
        headers={"Authorization": "Bearer token-user-receiver-verified"},
    )
    assert response.status_code == 403
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "INSUFFICIENT_ROLE"


def test_driver_cannot_access_donor_profile(client: TestClient):
    response = client.get(
        "/api/v1/donor/profile",
        headers={"Authorization": "Bearer token-user-driver-verified"},
    )
    assert response.status_code == 403
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "INSUFFICIENT_ROLE"


def test_receiver_can_access_receiver_profile(client: TestClient):
    response = client.get(
        "/api/v1/receiver/profile",
        headers={"Authorization": "Bearer token-user-receiver-verified"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["organization_name"] == "Feed Hope Foundation"


def test_donor_cannot_access_receiver_profile(client: TestClient):
    response = client.get(
        "/api/v1/receiver/profile",
        headers={"Authorization": "Bearer token-user-donor-verified"},
    )
    assert response.status_code == 403
    data = response.json()
    assert data["error"]["code"] == "INSUFFICIENT_ROLE"


def test_driver_can_access_driver_profile(client: TestClient):
    response = client.get(
        "/api/v1/driver/profile",
        headers={"Authorization": "Bearer token-user-driver-verified"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["vehicle_type"] == "Insulated Van"


def test_donor_cannot_access_driver_profile(client: TestClient):
    response = client.get(
        "/api/v1/driver/profile",
        headers={"Authorization": "Bearer token-user-donor-verified"},
    )
    assert response.status_code == 403
    data = response.json()
    assert data["error"]["code"] == "INSUFFICIENT_ROLE"
