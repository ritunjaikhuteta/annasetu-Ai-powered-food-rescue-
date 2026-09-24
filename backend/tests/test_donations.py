"""Tests for Surplus Food Donation API routes and validation."""

from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient


def get_time_offsets(avail_offset_hours: int = 1, deadline_offset_hours: int = 5):
    now = datetime.now(timezone.utc)
    avail = (now + timedelta(hours=avail_offset_hours)).isoformat()
    deadline = (now + timedelta(hours=deadline_offset_hours)).isoformat()
    prep = (now - timedelta(hours=1)).isoformat()
    return prep, avail, deadline


def test_donation_under_5kg_rejected(client: TestClient):
    prep, avail, deadline = get_time_offsets()
    payload = {
        "diet_type": "VEGETARIAN",
        "food_category_id": "cat-cooked-meals",
        "declared_quantity_kg": 4.5,  # Rejected: < 5 kg
        "preparation_at": prep,
        "available_from": avail,
        "rescue_deadline": deadline,
        "storage_condition": "refrigerated",
        "packaging_type": "Food-grade sealed containers",
        "raw_description": "Excess vegetarian thali meals",
        "pickup_location_id": "loc-donor-1",
    }
    res = client.post(
        "/api/v1/donations",
        headers={"Authorization": "Bearer token-user-donor-verified"},
        json=payload,
    )
    assert res.status_code == 422


def test_valid_donation_creation_and_posting(client: TestClient):
    prep, avail, deadline = get_time_offsets()
    payload = {
        "diet_type": "VEGETARIAN",
        "food_category_id": "cat-cooked-meals",
        "declared_quantity_kg": 40.0,
        "preparation_at": prep,
        "available_from": avail,
        "rescue_deadline": deadline,
        "storage_condition": "refrigerated",
        "packaging_type": "Food-grade sealed containers",
        "raw_description": "Freshly prepared vegetarian rice, dal, and vegetable curry",
        "pickup_location_id": "loc-donor-1",
    }
    create_res = client.post(
        "/api/v1/donations",
        headers={"Authorization": "Bearer token-user-donor-verified"},
        json=payload,
    )
    assert create_res.status_code == 201
    don = create_res.json()
    assert don["status"] == "DRAFT"
    assert don["declared_quantity_kg"] == 40.0
    assert don["remaining_quantity_kg"] == 40.0
    donation_id = don["id"]

    # Post donation
    post_res = client.post(
        f"/api/v1/donations/{donation_id}/post",
        headers={"Authorization": "Bearer token-user-donor-verified"},
    )
    assert post_res.status_code == 200
    posted = post_res.json()
    assert posted["status"] == "POSTED"


def test_invalid_pickup_location_rejected(client: TestClient):
    prep, avail, deadline = get_time_offsets()
    payload = {
        "diet_type": "VEGETARIAN",
        "food_category_id": "cat-cooked-meals",
        "declared_quantity_kg": 15.0,
        "preparation_at": prep,
        "available_from": avail,
        "rescue_deadline": deadline,
        "packaging_type": "Sealed boxes",
        "raw_description": "Fresh meals",
        "pickup_location_id": "loc-receiver-1",  # Belongs to receiver, not donor!
    }
    res = client.post(
        "/api/v1/donations",
        headers={"Authorization": "Bearer token-user-donor-verified"},
        json=payload,
    )
    assert res.status_code == 403
    assert res.json()["error"]["code"] == "LOCATION_FORBIDDEN"


def test_invalid_rescue_deadline_before_available_from(client: TestClient):
    now = datetime.now(timezone.utc)
    prep = (now - timedelta(hours=1)).isoformat()
    avail = (now + timedelta(hours=4)).isoformat()
    deadline = (now + timedelta(hours=2)).isoformat()  # Deadline is before available_from!

    payload = {
        "diet_type": "VEGETARIAN",
        "food_category_id": "cat-cooked-meals",
        "declared_quantity_kg": 20.0,
        "preparation_at": prep,
        "available_from": avail,
        "rescue_deadline": deadline,
        "packaging_type": "Sealed boxes",
        "raw_description": "Fresh meals",
        "pickup_location_id": "loc-donor-1",
    }
    res = client.post(
        "/api/v1/donations",
        headers={"Authorization": "Bearer token-user-donor-verified"},
        json=payload,
    )
    assert res.status_code == 422


def test_unauthorized_receiver_cannot_create_donation(client: TestClient):
    prep, avail, deadline = get_time_offsets()
    payload = {
        "diet_type": "VEGETARIAN",
        "food_category_id": "cat-cooked-meals",
        "declared_quantity_kg": 20.0,
        "preparation_at": prep,
        "available_from": avail,
        "rescue_deadline": deadline,
        "packaging_type": "Sealed boxes",
        "raw_description": "Fresh meals",
        "pickup_location_id": "loc-donor-1",
    }
    res = client.post(
        "/api/v1/donations",
        headers={"Authorization": "Bearer token-user-receiver-verified"},
        json=payload,
    )
    assert res.status_code == 403
    assert res.json()["error"]["code"] == "INSUFFICIENT_ROLE"
