"""Tests for Donation Allocation Engine and Concurrency Protection."""

import asyncio
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient


def get_offsets():
    now = datetime.now(timezone.utc)
    return (
        (now - timedelta(hours=1)).isoformat(),
        (now + timedelta(hours=1)).isoformat(),
        (now + timedelta(hours=6)).isoformat(),
    )


def test_sequential_canonical_allocation_flow(client: TestClient):
    """Verifies canonical 40 kg allocation split: 10 kg + 12 kg + 18 kg = 40 kg total.

    Validates exact remaining quantity decrements and state transitions:
    Donation: POSTED -> MATCHED -> ALLOCATED (0 kg remaining)
    Needs: ACTIVE -> FULFILLED
    """
    prep, avail, deadline = get_offsets()

    # 1. Create a 40 kg Donation
    d_res = client.post(
        "/api/v1/donations",
        headers={"Authorization": "Bearer token-user-donor-verified"},
        json={
            "diet_type": "VEGETARIAN",
            "food_category_id": "cat-cooked-meals",
            "declared_quantity_kg": 40.0,
            "preparation_at": prep,
            "available_from": avail,
            "rescue_deadline": deadline,
            "packaging_type": "Food-grade containers",
            "raw_description": "Bulk surplus thali meals",
            "pickup_location_id": "loc-donor-1",
        },
    )
    donation_id = d_res.json()["id"]
    client.post(f"/api/v1/donations/{donation_id}/post", headers={"Authorization": "Bearer token-user-donor-verified"})

    # 2. Create Need 1 (requires 10 kg)
    n1_res = client.post(
        "/api/v1/needs",
        headers={"Authorization": "Bearer token-user-receiver-verified"},
        json={
            "meal_period": "DINNER",
            "diet_type": "VEGETARIAN",
            "food_category_id": "cat-cooked-meals",
            "required_quantity_kg": 10.0,
            "minimum_quantity_kg": 5.0,
            "receiving_capacity_kg": 20.0,
            "required_by": (datetime.now(timezone.utc) + timedelta(hours=7)).isoformat(),
            "location_id": "loc-receiver-1",
        },
    )
    need1_id = n1_res.json()["id"]
    client.post(f"/api/v1/needs/{need1_id}/activate", headers={"Authorization": "Bearer token-user-receiver-verified"})

    # 3. Create Need 2 (requires 12 kg)
    n2_res = client.post(
        "/api/v1/needs",
        headers={"Authorization": "Bearer token-user-receiver-verified"},
        json={
            "meal_period": "DINNER",
            "diet_type": "VEGETARIAN",
            "food_category_id": "cat-cooked-meals",
            "required_quantity_kg": 12.0,
            "minimum_quantity_kg": 5.0,
            "receiving_capacity_kg": 25.0,
            "required_by": (datetime.now(timezone.utc) + timedelta(hours=7)).isoformat(),
            "location_id": "loc-receiver-1",
        },
    )
    need2_id = n2_res.json()["id"]
    client.post(f"/api/v1/needs/{need2_id}/activate", headers={"Authorization": "Bearer token-user-receiver-verified"})

    # 4. Create Need 3 (requires 25 kg, will receive 18 kg)
    n3_res = client.post(
        "/api/v1/needs",
        headers={"Authorization": "Bearer token-user-receiver-verified"},
        json={
            "meal_period": "DINNER",
            "diet_type": "VEGETARIAN",
            "food_category_id": "cat-cooked-meals",
            "required_quantity_kg": 25.0,
            "minimum_quantity_kg": 5.0,
            "receiving_capacity_kg": 50.0,
            "required_by": (datetime.now(timezone.utc) + timedelta(hours=7)).isoformat(),
            "location_id": "loc-receiver-1",
        },
    )
    need3_id = n3_res.json()["id"]
    client.post(f"/api/v1/needs/{need3_id}/activate", headers={"Authorization": "Bearer token-user-receiver-verified"})

    # Allocation 1: 10 kg -> Need 1
    alloc1_res = client.post(
        "/api/v1/allocations",
        headers={"Authorization": "Bearer token-user-donor-verified"},
        json={"donation_id": donation_id, "need_id": need1_id, "allocated_quantity_kg": 10.0},
    )
    assert alloc1_res.status_code == 201
    assert alloc1_res.json()["status"] == "RESERVED"

    # Verify Need 1 is now FULFILLED (remaining = 0)
    need1 = client.get(f"/api/v1/needs/{need1_id}", headers={"Authorization": "Bearer token-user-receiver-verified"}).json()
    assert need1["remaining_quantity_kg"] == 0.0
    assert need1["status"] == "FULFILLED"

    # Verify donation remaining = 30 kg, status = MATCHED
    don_state1 = client.get(f"/api/v1/donations/{donation_id}", headers={"Authorization": "Bearer token-user-donor-verified"}).json()
    assert don_state1["remaining_quantity_kg"] == 30.0
    assert don_state1["status"] == "MATCHED"

    # Allocation 2: 12 kg -> Need 2
    alloc2_res = client.post(
        "/api/v1/allocations",
        headers={"Authorization": "Bearer token-user-donor-verified"},
        json={"donation_id": donation_id, "need_id": need2_id, "allocated_quantity_kg": 12.0},
    )
    assert alloc2_res.status_code == 201

    need2 = client.get(f"/api/v1/needs/{need2_id}", headers={"Authorization": "Bearer token-user-receiver-verified"}).json()
    assert need2["remaining_quantity_kg"] == 0.0
    assert need2["status"] == "FULFILLED"

    don_state2 = client.get(f"/api/v1/donations/{donation_id}", headers={"Authorization": "Bearer token-user-donor-verified"}).json()
    assert don_state2["remaining_quantity_kg"] == 18.0

    # Allocation 3: 18 kg -> Need 3
    alloc3_res = client.post(
        "/api/v1/allocations",
        headers={"Authorization": "Bearer token-user-donor-verified"},
        json={"donation_id": donation_id, "need_id": need3_id, "allocated_quantity_kg": 18.0},
    )
    assert alloc3_res.status_code == 201

    # Need 3 was 25 kg, received 18 kg -> remaining 7 kg, status = PARTIALLY_FULFILLED
    need3 = client.get(f"/api/v1/needs/{need3_id}", headers={"Authorization": "Bearer token-user-receiver-verified"}).json()
    assert need3["remaining_quantity_kg"] == 7.0
    assert need3["status"] == "PARTIALLY_FULFILLED"

    # Donation is now 0 kg remaining -> status = ALLOCATED
    don_state3 = client.get(f"/api/v1/donations/{donation_id}", headers={"Authorization": "Bearer token-user-donor-verified"}).json()
    assert don_state3["remaining_quantity_kg"] == 0.0
    assert don_state3["status"] == "ALLOCATED"


def test_over_allocation_strictly_prevented(client: TestClient):
    prep, avail, deadline = get_offsets()

    # 10 kg Donation
    d_res = client.post(
        "/api/v1/donations",
        headers={"Authorization": "Bearer token-user-donor-verified"},
        json={
            "diet_type": "VEGETARIAN",
            "food_category_id": "cat-cooked-meals",
            "declared_quantity_kg": 10.0,
            "preparation_at": prep,
            "available_from": avail,
            "rescue_deadline": deadline,
            "packaging_type": "Boxes",
            "raw_description": "Cooked meals",
            "pickup_location_id": "loc-donor-1",
        },
    )
    donation_id = d_res.json()["id"]
    client.post(f"/api/v1/donations/{donation_id}/post", headers={"Authorization": "Bearer token-user-donor-verified"})

    # 20 kg Need
    n_res = client.post(
        "/api/v1/needs",
        headers={"Authorization": "Bearer token-user-receiver-verified"},
        json={
            "meal_period": "DINNER",
            "diet_type": "VEGETARIAN",
            "food_category_id": "cat-cooked-meals",
            "required_quantity_kg": 20.0,
            "minimum_quantity_kg": 5.0,
            "receiving_capacity_kg": 30.0,
            "required_by": (datetime.now(timezone.utc) + timedelta(hours=7)).isoformat(),
            "location_id": "loc-receiver-1",
        },
    )
    need_id = n_res.json()["id"]
    client.post(f"/api/v1/needs/{need_id}/activate", headers={"Authorization": "Bearer token-user-receiver-verified"})

    # Attempt to allocate 15 kg when only 10 kg is available
    res = client.post(
        "/api/v1/allocations",
        headers={"Authorization": "Bearer token-user-donor-verified"},
        json={"donation_id": donation_id, "need_id": need_id, "allocated_quantity_kg": 15.0},
    )
    assert res.status_code == 409
    assert res.json()["error"]["code"] == "QUANTITY_EXCEEDED"
