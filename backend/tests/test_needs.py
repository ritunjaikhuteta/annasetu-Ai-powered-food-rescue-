"""Tests for NGO Need API routes and validation."""

from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient


def get_future_iso(hours: int = 5) -> str:
    return (datetime.now(timezone.utc) + timedelta(hours=hours)).isoformat()


def get_past_iso(hours: int = 5) -> str:
    return (datetime.now(timezone.utc) - timedelta(hours=hours)).isoformat()


def test_valid_need_creation_and_activation(client: TestClient):
    # 1. Create Need in DRAFT status
    payload = {
        "meal_period": "DINNER",
        "diet_type": "VEGETARIAN",
        "food_category_id": "cat-cooked-meals",
        "required_quantity_kg": 30.0,
        "minimum_quantity_kg": 10.0,
        "receiving_capacity_kg": 50.0,
        "required_by": get_future_iso(6),
        "receiving_start_time": "18:00",
        "receiving_end_time": "21:00",
        "location_id": "loc-receiver-1",
        "special_requirements": "Nutritious cooked meals for evening shelter distribution",
    }

    create_res = client.post(
        "/api/v1/needs",
        headers={"Authorization": "Bearer token-user-receiver-verified"},
        json=payload,
    )
    assert create_res.status_code == 201
    need = create_res.json()
    assert need["status"] == "DRAFT"
    assert need["required_quantity_kg"] == 30.0
    assert need["remaining_quantity_kg"] == 30.0
    need_id = need["id"]

    # 2. Activate Need
    act_res = client.post(
        f"/api/v1/needs/{need_id}/activate",
        headers={"Authorization": "Bearer token-user-receiver-verified"},
    )
    assert act_res.status_code == 200
    activated = act_res.json()
    assert activated["status"] == "ACTIVE"


def test_invalid_need_quantity_relationships_rejected(client: TestClient):
    # minimum_quantity > required_quantity must be rejected
    payload = {
        "meal_period": "LUNCH",
        "diet_type": "VEGETARIAN",
        "food_category_id": "cat-cooked-meals",
        "required_quantity_kg": 20.0,
        "minimum_quantity_kg": 25.0,  # Invalid: > required_quantity
        "receiving_capacity_kg": 50.0,
        "required_by": get_future_iso(4),
        "location_id": "loc-receiver-1",
    }
    res = client.post(
        "/api/v1/needs",
        headers={"Authorization": "Bearer token-user-receiver-verified"},
        json=payload,
    )
    assert res.status_code == 422


def test_invalid_receiving_location_ownership_rejected(client: TestClient):
    # Receiver trying to use another user's location
    payload = {
        "meal_period": "LUNCH",
        "diet_type": "VEGETARIAN",
        "food_category_id": "cat-cooked-meals",
        "required_quantity_kg": 20.0,
        "minimum_quantity_kg": 5.0,
        "receiving_capacity_kg": 30.0,
        "required_by": get_future_iso(4),
        "location_id": "loc-donor-1",  # Belongs to donor, not receiver!
    }
    res = client.post(
        "/api/v1/needs",
        headers={"Authorization": "Bearer token-user-receiver-verified"},
        json=payload,
    )
    assert res.status_code == 403
    assert res.json()["error"]["code"] == "LOCATION_FORBIDDEN"


def test_unauthorized_donor_cannot_create_need(client: TestClient):
    payload = {
        "meal_period": "LUNCH",
        "diet_type": "VEGETARIAN",
        "food_category_id": "cat-cooked-meals",
        "required_quantity_kg": 20.0,
        "minimum_quantity_kg": 5.0,
        "receiving_capacity_kg": 30.0,
        "required_by": get_future_iso(4),
        "location_id": "loc-receiver-1",
    }
    res = client.post(
        "/api/v1/needs",
        headers={"Authorization": "Bearer token-user-donor-verified"},
        json=payload,
    )
    assert res.status_code == 403
    assert res.json()["error"]["code"] == "INSUFFICIENT_ROLE"


def test_activate_need_with_past_deadline_rejected(client: TestClient):
    payload = {
        "meal_period": "LUNCH",
        "diet_type": "VEGETARIAN",
        "food_category_id": "cat-cooked-meals",
        "required_quantity_kg": 20.0,
        "minimum_quantity_kg": 5.0,
        "receiving_capacity_kg": 30.0,
        "required_by": get_past_iso(2),  # In the past
        "location_id": "loc-receiver-1",
    }
    create_res = client.post(
        "/api/v1/needs",
        headers={"Authorization": "Bearer token-user-receiver-verified"},
        json=payload,
    )
    need_id = create_res.json()["id"]

    act_res = client.post(
        f"/api/v1/needs/{need_id}/activate",
        headers={"Authorization": "Bearer token-user-receiver-verified"},
    )
    assert act_res.status_code == 422
    assert act_res.json()["error"]["code"] == "DEADLINE_IN_PAST"
