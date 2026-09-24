"""Tests for Profile retrieval, updates, and validation."""

from fastapi.testclient import TestClient


def test_get_my_profile(client: TestClient):
    response = client.get(
        "/api/v1/me/profile",
        headers={"Authorization": "Bearer token-user-donor-verified"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["full_name"] == "Verified Donor Chef"
    assert data["role"] == "DONOR"


def test_update_my_profile(client: TestClient):
    response = client.patch(
        "/api/v1/me/profile",
        headers={"Authorization": "Bearer token-user-donor-verified"},
        json={"full_name": "Updated Chef Name", "phone": "+919999888877"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["full_name"] == "Updated Chef Name"
    assert data["phone"] == "+919999888877"


def test_update_donor_profile_safe_fields(client: TestClient):
    response = client.patch(
        "/api/v1/donor/profile",
        headers={"Authorization": "Bearer token-user-donor-pending"},
        json={
            "business_name": "Updated Kitchen Name",
            # Attempt to smuggle verification status tampering:
            "verification_status": "VERIFIED",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["business_name"] == "Updated Kitchen Name"
    # Verification status MUST remain PENDING - tampering is completely ignored
    assert data["verification_status"] == "PENDING"


def test_update_receiver_profile_safe_fields(client: TestClient):
    response = client.patch(
        "/api/v1/receiver/profile",
        headers={"Authorization": "Bearer token-user-receiver-verified"},
        json={
            "organization_name": "Updated NGO Relief",
            "has_refrigeration": True,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["organization_name"] == "Updated NGO Relief"


def test_update_driver_profile_safe_fields(client: TestClient):
    response = client.patch(
        "/api/v1/driver/profile",
        headers={"Authorization": "Bearer token-user-driver-verified"},
        json={
            "vehicle_type": "Refrigerated Van",
            "is_online": False,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["vehicle_type"] == "Refrigerated Van"
    assert data["is_online"] is False


def test_validation_error_driver_latitude(client: TestClient):
    # latitude must be between -90 and 90
    response = client.patch(
        "/api/v1/driver/profile",
        headers={"Authorization": "Bearer token-user-driver-verified"},
        json={"current_latitude": 150.0},
    )
    assert response.status_code == 422
    data = response.json()
    assert data["success"] is False
    assert data["error"]["code"] == "VALIDATION_ERROR"
