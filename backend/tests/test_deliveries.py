"""Phase 13 Delivery & Driver Operations Test Suite."""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict
import pytest
from fastapi.testclient import TestClient
from tests.conftest import MockSupabaseClient


def seed_test_rescue(db: MockSupabaseClient) -> Dict[str, Any]:
    """Helper to seed a complete donation with 2 reserved allocations."""
    now = datetime.now(timezone.utc)
    rescue_deadline = (now + timedelta(hours=4)).isoformat()
    required_by = (now + timedelta(hours=3)).isoformat()

    # Create donation
    donation_id = "don-delivery-1"
    db.donations[donation_id] = {
        "id": donation_id,
        "donor_id": "user-donor-verified",
        "title": "Fresh Vegetable Biryani",
        "pickup_location_id": "loc-donor-1",
        "total_quantity_kg": 60.0,
        "available_quantity_kg": 0.0,
        "rescue_deadline": rescue_deadline,
        "status": "ALLOCATED",
    }

    # Create Need 1
    need_1_id = "need-deliv-1"
    db.ngo_needs[need_1_id] = {
        "id": need_1_id,
        "receiver_id": "rp-1",
        "location_id": "loc-receiver-1",
        "required_quantity_kg": 30.0,
        "fulfilled_quantity_kg": 30.0,
        "required_by": required_by,
        "status": "MATCHED",
    }

    # Create Need 2
    need_2_id = "need-deliv-2"
    db.ngo_needs[need_2_id] = {
        "id": need_2_id,
        "receiver_id": "rp-1",
        "location_id": "loc-receiver-1",
        "required_quantity_kg": 30.0,
        "fulfilled_quantity_kg": 30.0,
        "required_by": required_by,
        "status": "MATCHED",
    }

    # Allocation 1
    alloc_1_id = "alloc-deliv-1"
    db.donation_allocations[alloc_1_id] = {
        "id": alloc_1_id,
        "donation_id": donation_id,
        "need_id": need_1_id,
        "allocated_quantity_kg": 30.0,
        "status": "RESERVED",
    }

    # Allocation 2
    alloc_2_id = "alloc-deliv-2"
    db.donation_allocations[alloc_2_id] = {
        "id": alloc_2_id,
        "donation_id": donation_id,
        "need_id": need_2_id,
        "allocated_quantity_kg": 30.0,
        "status": "ACCEPTED",
    }

    return {
        "donation_id": donation_id,
        "alloc_1_id": alloc_1_id,
        "alloc_2_id": alloc_2_id,
    }


def seed_second_driver(db: MockSupabaseClient) -> str:
    """Helper to seed a second verified driver for concurrency tests."""
    driver_2_user_id = "user-driver-2"
    db.profiles[driver_2_user_id] = {
        "id": driver_2_user_id,
        "full_name": "Second Partner Driver",
        "phone": "+919876543299",
        "role": "DRIVER",
        "is_active": True,
    }
    db.driver_profiles[driver_2_user_id] = {
        "id": "drp-2",
        "user_id": driver_2_user_id,
        "vehicle_type": "van",
        "vehicle_number": "DL-01-CD-5678",
        "vehicle_capacity_kg": 500.0,
        "is_online": True,
        "availability_status": "AVAILABLE",
        "verification_status": "VERIFIED",
        "current_latitude": 28.6140,
        "current_longitude": 77.2091,
    }
    return driver_2_user_id


def test_create_delivery_success(client: TestClient, mock_db: MockSupabaseClient):
    """Test creating a multi-stop delivery from reserved allocations."""
    seed = seed_test_rescue(mock_db)

    response = client.post(
        "/api/v1/deliveries",
        headers={"Authorization": "Bearer token-user-donor-verified"},
        json={
            "donation_id": seed["donation_id"],
            "allocation_ids": [seed["alloc_1_id"], seed["alloc_2_id"]],
        },
    )

    assert response.status_code == 201
    data = response.json()
    assert data["donation_id"] == seed["donation_id"]
    assert data["status"] == "OPEN"
    assert data["total_quantity_kg"] == 60.0
    assert data["total_distance_km"] > 0
    assert data["estimated_duration_minutes"] > 0

    # Verify stops: 1 pickup + 2 delivery stops
    stops = data["stops"]
    assert len(stops) == 3
    assert stops[0]["sequence_number"] == 1
    assert stops[0]["stop_type"] == "PICKUP"
    assert stops[0]["quantity_kg"] == 60.0

    assert stops[1]["sequence_number"] == 2
    assert stops[1]["stop_type"] == "DELIVERY"

    assert stops[2]["sequence_number"] == 3
    assert stops[2]["stop_type"] == "DELIVERY"


def test_create_delivery_validation_failures(client: TestClient, mock_db: MockSupabaseClient):
    """Test rejection of invalid delivery creations."""
    seed = seed_test_rescue(mock_db)

    # 1. Non-existent donation
    res_fake = client.post(
        "/api/v1/deliveries",
        headers={"Authorization": "Bearer token-user-donor-verified"},
        json={"donation_id": "non-existent", "allocation_ids": [seed["alloc_1_id"]]},
    )
    assert res_fake.status_code == 404

    # 2. Allocation does not belong to donation
    other_alloc_id = "alloc-other"
    mock_db.donation_allocations[other_alloc_id] = {
        "id": other_alloc_id,
        "donation_id": "other-donation",
        "need_id": "need-deliv-1",
        "allocated_quantity_kg": 10.0,
        "status": "ACCEPTED",
    }
    res_mismatch = client.post(
        "/api/v1/deliveries",
        headers={"Authorization": "Bearer token-user-donor-verified"},
        json={"donation_id": seed["donation_id"], "allocation_ids": [other_alloc_id]},
    )
    assert res_mismatch.status_code == 422

    # 3. Allocation in invalid state (CANCELLED)
    cancelled_alloc = "alloc-cancelled"
    mock_db.donation_allocations[cancelled_alloc] = {
        "id": cancelled_alloc,
        "donation_id": seed["donation_id"],
        "need_id": "need-deliv-1",
        "allocated_quantity_kg": 10.0,
        "status": "CANCELLED",
    }
    res_invalid_status = client.post(
        "/api/v1/deliveries",
        headers={"Authorization": "Bearer token-user-donor-verified"},
        json={"donation_id": seed["donation_id"], "allocation_ids": [cancelled_alloc]},
    )
    assert res_invalid_status.status_code == 409


def test_create_delivery_max_stops_limit(client: TestClient, mock_db: MockSupabaseClient):
    """Test rejecting delivery missions with >3 stops for MVP."""
    seed = seed_test_rescue(mock_db)
    four_allocs = ["a1", "a2", "a3", "a4"]

    response = client.post(
        "/api/v1/deliveries",
        headers={"Authorization": "Bearer token-user-donor-verified"},
        json={"donation_id": seed["donation_id"], "allocation_ids": four_allocs},
    )
    assert response.status_code == 422


def test_create_delivery_deadline_conflict(client: TestClient, mock_db: MockSupabaseClient):
    """Test rejecting delivery when rescue deadline is in the past / unfeasible."""
    seed = seed_test_rescue(mock_db)
    # Set rescue deadline in the past
    mock_db.donations[seed["donation_id"]]["rescue_deadline"] = (
        datetime.now(timezone.utc) - timedelta(minutes=10)
    ).isoformat()

    response = client.post(
        "/api/v1/deliveries",
        headers={"Authorization": "Bearer token-user-donor-verified"},
        json={"donation_id": seed["donation_id"], "allocation_ids": [seed["alloc_1_id"]]},
    )
    assert response.status_code == 409
    err = response.json()["error"]
    assert "No feasible route" in err["message"]


def test_eligible_drivers_discovery_and_ranking(client: TestClient, mock_db: MockSupabaseClient):
    """Test discovery and deterministic ranking of eligible drivers."""
    seed = seed_test_rescue(mock_db)
    seed_second_driver(mock_db)

    # Create delivery
    deliv_res = client.post(
        "/api/v1/deliveries",
        headers={"Authorization": "Bearer token-user-donor-verified"},
        json={"donation_id": seed["donation_id"], "allocation_ids": [seed["alloc_1_id"]]},
    )
    delivery_id = deliv_res.json()["id"]

    # Discover eligible drivers
    drivers_res = client.get(
        f"/api/v1/deliveries/{delivery_id}/eligible-drivers",
        headers={"Authorization": "Bearer token-user-donor-verified"},
    )
    assert drivers_res.status_code == 200
    drivers = drivers_res.json()
    assert len(drivers) >= 2

    # Check vehicle capacity filtering: if a driver vehicle capacity is < 30kg, they are excluded
    underweight_driver = "user-driver-scooter"
    mock_db.profiles[underweight_driver] = {
        "id": underweight_driver,
        "full_name": "Scooter Partner",
        "phone": "+919876543288",
        "role": "DRIVER",
        "is_active": True,
    }
    mock_db.driver_profiles[underweight_driver] = {
        "id": "drp-scooter",
        "user_id": underweight_driver,
        "vehicle_type": "scooter",
        "vehicle_capacity_kg": 15.0,  # Less than 30kg delivery
        "is_online": True,
        "availability_status": "AVAILABLE",
        "verification_status": "VERIFIED",
        "current_latitude": 28.6141,
        "current_longitude": 77.2092,
    }

    refreshed_drivers = client.get(
        f"/api/v1/deliveries/{delivery_id}/eligible-drivers",
        headers={"Authorization": "Bearer token-user-donor-verified"},
    ).json()

    driver_user_ids = [d["driver_user_id"] for d in refreshed_drivers]
    assert underweight_driver not in driver_user_ids


def test_driver_offers_and_view_decline(client: TestClient, mock_db: MockSupabaseClient):
    """Test dispatching offers and view/decline transitions."""
    seed = seed_test_rescue(mock_db)
    deliv = client.post(
        "/api/v1/deliveries",
        headers={"Authorization": "Bearer token-user-donor-verified"},
        json={"donation_id": seed["donation_id"], "allocation_ids": [seed["alloc_1_id"]]},
    ).json()
    delivery_id = deliv["id"]

    # Dispatch offers
    offers_res = client.post(
        f"/api/v1/deliveries/{delivery_id}/offers",
        headers={"Authorization": "Bearer token-user-donor-verified"},
    )
    assert offers_res.status_code == 200
    offers = offers_res.json()
    assert len(offers) > 0
    offer = offers[0]
    offer_id = offer["id"]
    assert offer["status"] == "OFFERED"
    assert offer["offered_delivery_charge"] > 0
    assert offer["estimated_driver_payout"] > 0

    # Driver views offer
    view_res = client.post(
        f"/api/v1/delivery-offers/{offer_id}/view",
        headers={"Authorization": "Bearer token-user-driver-verified"},
    )
    assert view_res.status_code == 200
    assert view_res.json()["status"] == "VIEWED"

    # Driver declines offer
    decline_res = client.post(
        f"/api/v1/delivery-offers/{offer_id}/decline",
        headers={"Authorization": "Bearer token-user-driver-verified"},
    )
    assert decline_res.status_code == 200
    assert decline_res.json()["status"] == "DECLINED"


def test_concurrent_offer_acceptance(client: TestClient, mock_db: MockSupabaseClient):
    """Test that exactly one driver wins the assignment and others are rejected."""
    seed = seed_test_rescue(mock_db)
    driver_2 = seed_second_driver(mock_db)

    deliv = client.post(
        "/api/v1/deliveries",
        headers={"Authorization": "Bearer token-user-donor-verified"},
        json={"donation_id": seed["donation_id"], "allocation_ids": [seed["alloc_1_id"]]},
    ).json()
    delivery_id = deliv["id"]

    offers = client.post(
        f"/api/v1/deliveries/{delivery_id}/offers",
        headers={"Authorization": "Bearer token-user-donor-verified"},
    ).json()

    offer_1 = next(o for o in offers if o["driver_id"] == "drp-1")
    offer_2 = next(o for o in offers if o["driver_id"] == "drp-2")

    # Driver 1 accepts
    acc_res = client.post(
        f"/api/v1/delivery-offers/{offer_1['id']}/accept",
        headers={"Authorization": "Bearer token-user-driver-verified"},
    )
    assert acc_res.status_code == 200
    accepted_deliv = acc_res.json()
    assert accepted_deliv["status"] == "ACCEPTED"
    assert accepted_deliv["driver_id"] == "drp-1"

    # Verify Driver 1 became ON_JOB
    drp_1 = mock_db.driver_profiles["user-driver-verified"]
    assert drp_1["availability_status"] == "ON_JOB"

    # Second driver attempts to accept -> Must be rejected with 409 Conflict
    acc_2_res = client.post(
        f"/api/v1/delivery-offers/{offer_2['id']}/accept",
        headers={"Authorization": f"Bearer token-{driver_2}"},
    )
    assert acc_2_res.status_code == 409
    assert acc_2_res.json()["error"]["code"] == "DELIVERY_TAKEN"


def test_driver_cancellation_triggers_reassignment(client: TestClient, mock_db: MockSupabaseClient):
    """Test driver cancellation triggers REASSIGNMENT_REQUIRED and frees driver."""
    seed = seed_test_rescue(mock_db)
    deliv = client.post(
        "/api/v1/deliveries",
        headers={"Authorization": "Bearer token-user-donor-verified"},
        json={"donation_id": seed["donation_id"], "allocation_ids": [seed["alloc_1_id"]]},
    ).json()
    delivery_id = deliv["id"]

    offers = client.post(
        f"/api/v1/deliveries/{delivery_id}/offers",
        headers={"Authorization": "Bearer token-user-donor-verified"},
    ).json()

    # Accept
    client.post(
        f"/api/v1/delivery-offers/{offers[0]['id']}/accept",
        headers={"Authorization": "Bearer token-user-driver-verified"},
    )

    # Driver cancels
    cancel_res = client.post(
        f"/api/v1/deliveries/{delivery_id}/cancel",
        headers={"Authorization": "Bearer token-user-driver-verified"},
    )
    assert cancel_res.status_code == 200
    assert cancel_res.json()["status"] == "REASSIGNMENT_REQUIRED"

    # Driver should be freed back to AVAILABLE
    drp_1 = mock_db.driver_profiles["user-driver-verified"]
    assert drp_1["availability_status"] == "AVAILABLE"


def test_delivery_state_machine_strict_transitions(client: TestClient, mock_db: MockSupabaseClient):
    """Test complete forward delivery lifecycle and rejection of illegal jumps."""
    seed = seed_test_rescue(mock_db)
    deliv = client.post(
        "/api/v1/deliveries",
        headers={"Authorization": "Bearer token-user-donor-verified"},
        json={"donation_id": seed["donation_id"], "allocation_ids": [seed["alloc_1_id"]]},
    ).json()
    delivery_id = deliv["id"]

    offers = client.post(
        f"/api/v1/deliveries/{delivery_id}/offers",
        headers={"Authorization": "Bearer token-user-donor-verified"},
    ).json()

    # 1. OPEN -> ACCEPTED
    client.post(
        f"/api/v1/delivery-offers/{offers[0]['id']}/accept",
        headers={"Authorization": "Bearer token-user-driver-verified"},
    )

    # Illegal jump: ACCEPTED -> DELIVERED (Must be 409)
    illegal_res = client.post(
        f"/api/v1/deliveries/{delivery_id}/complete-stop",
        headers={"Authorization": "Bearer token-user-driver-verified"},
    )
    assert illegal_res.status_code == 409
    assert illegal_res.json()["error"]["code"] == "INVALID_STATE_TRANSITION"

    # 2. ACCEPTED -> ARRIVING_PICKUP
    arr_res = client.post(
        f"/api/v1/deliveries/{delivery_id}/arrive-pickup",
        headers={"Authorization": "Bearer token-user-driver-verified"},
        json={"latitude": 28.6139, "longitude": 77.2090},
    )
    assert arr_res.status_code == 200
    assert arr_res.json()["status"] == "ARRIVING_PICKUP"

    # 3. ARRIVING_PICKUP -> PICKED_UP
    pickup_res = client.post(
        f"/api/v1/deliveries/{delivery_id}/mark-picked-up",
        headers={"Authorization": "Bearer token-user-driver-verified"},
    )
    assert pickup_res.status_code == 200
    assert pickup_res.json()["status"] == "PICKED_UP"

    # 4. PICKED_UP -> IN_TRANSIT
    transit_res = client.post(
        f"/api/v1/deliveries/{delivery_id}/start-transit",
        headers={"Authorization": "Bearer token-user-driver-verified"},
    )
    assert transit_res.status_code == 200
    assert transit_res.json()["status"] == "IN_TRANSIT"

    # 5. IN_TRANSIT -> AT_STOP
    stop_res = client.post(
        f"/api/v1/deliveries/{delivery_id}/arrive-stop",
        headers={"Authorization": "Bearer token-user-driver-verified"},
        json={"latitude": 28.5672, "longitude": 77.1982},
    )
    assert stop_res.status_code == 200
    assert stop_res.json()["status"] == "AT_STOP"

    # 6. AT_STOP -> DELIVERED
    delivered_res = client.post(
        f"/api/v1/deliveries/{delivery_id}/complete-stop",
        headers={"Authorization": "Bearer token-user-driver-verified"},
    )
    assert delivered_res.status_code == 200
    assert delivered_res.json()["status"] == "DELIVERED"

    # Driver should be AVAILABLE again
    drp = mock_db.driver_profiles["user-driver-verified"]
    assert drp["availability_status"] == "AVAILABLE"


def test_unauthorized_driver_actions_forbidden(client: TestClient, mock_db: MockSupabaseClient):
    """Test that unauthorized users or other drivers cannot perform delivery transitions."""
    seed = seed_test_rescue(mock_db)
    driver_2 = seed_second_driver(mock_db)

    deliv = client.post(
        "/api/v1/deliveries",
        headers={"Authorization": "Bearer token-user-donor-verified"},
        json={"donation_id": seed["donation_id"], "allocation_ids": [seed["alloc_1_id"]]},
    ).json()
    delivery_id = deliv["id"]

    offers = client.post(
        f"/api/v1/deliveries/{delivery_id}/offers",
        headers={"Authorization": "Bearer token-user-donor-verified"},
    ).json()

    # Assigned to Driver 1
    client.post(
        f"/api/v1/delivery-offers/{offers[0]['id']}/accept",
        headers={"Authorization": "Bearer token-user-driver-verified"},
    )

    # Driver 2 attempts to perform arrive-pickup -> 403 Forbidden
    unauth_driver = client.post(
        f"/api/v1/deliveries/{delivery_id}/arrive-pickup",
        headers={"Authorization": f"Bearer token-{driver_2}"},
        json={"latitude": 28.6139, "longitude": 77.2090},
    )
    assert unauth_driver.status_code == 403

    # Receiver attempts driver action -> 403 Forbidden
    receiver_attempt = client.post(
        f"/api/v1/deliveries/{delivery_id}/arrive-pickup",
        headers={"Authorization": "Bearer token-user-receiver-verified"},
    )
    assert receiver_attempt.status_code == 403


def test_driver_location_telemetry_and_gps_proximity(client: TestClient, mock_db: MockSupabaseClient):
    """Test driver GPS location telemetry update and proximity enforcement."""
    # 1. Update location
    loc_res = client.post(
        "/api/v1/driver/location",
        headers={"Authorization": "Bearer token-user-driver-verified"},
        json={
            "latitude": 28.6139,
            "longitude": 77.2090,
            "accuracy_meters": 5.0,
        },
    )
    assert loc_res.status_code == 201
    loc_data = loc_res.json()
    assert loc_data["latitude"] == 28.6139
    assert loc_data["longitude"] == 77.2090

    # 2. Invalid latitude validation failure
    invalid_loc = client.post(
        "/api/v1/driver/location",
        headers={"Authorization": "Bearer token-user-driver-verified"},
        json={"latitude": 120.0, "longitude": 77.2090},
    )
    assert invalid_loc.status_code == 422

    # 3. GPS Proximity enforcement on arrive-pickup
    seed = seed_test_rescue(mock_db)
    deliv = client.post(
        "/api/v1/deliveries",
        headers={"Authorization": "Bearer token-user-donor-verified"},
        json={"donation_id": seed["donation_id"], "allocation_ids": [seed["alloc_1_id"]]},
    ).json()
    delivery_id = deliv["id"]

    offers = client.post(
        f"/api/v1/deliveries/{delivery_id}/offers",
        headers={"Authorization": "Bearer token-user-donor-verified"},
    ).json()

    client.post(
        f"/api/v1/delivery-offers/{offers[0]['id']}/accept",
        headers={"Authorization": "Bearer token-user-driver-verified"},
    )

    # Driver attempts arrive-pickup from 50 km away (Gurgaon) -> Must be rejected with 409
    far_proximity_res = client.post(
        f"/api/v1/deliveries/{delivery_id}/arrive-pickup",
        headers={"Authorization": "Bearer token-user-driver-verified"},
        json={"latitude": 28.4595, "longitude": 77.0266},
    )
    assert far_proximity_res.status_code == 409
    assert far_proximity_res.json()["error"]["code"] == "PROXIMITY_CHECK_FAILED"
