"""Phase 14 Trust & Handoff Verification Test Suite."""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict
import pytest
from fastapi.testclient import TestClient
from tests.conftest import MockSupabaseClient


def setup_verified_delivery(client: TestClient, db: MockSupabaseClient) -> Dict[str, Any]:
    """Helper to setup a ready delivery assigned to user-driver-verified at ARRIVING_PICKUP state."""
    now = datetime.now(timezone.utc)
    rescue_deadline = (now + timedelta(hours=4)).isoformat()
    required_by = (now + timedelta(hours=3)).isoformat()

    donation_id = "don-handoff-1"
    db.donations[donation_id] = {
        "id": donation_id,
        "donor_id": "user-donor-verified",
        "title": "50 Portions Dal Makhani",
        "pickup_location_id": "loc-donor-1",
        "total_quantity_kg": 40.0,
        "available_quantity_kg": 0.0,
        "rescue_deadline": rescue_deadline,
        "status": "ALLOCATED",
    }

    # Need 1
    need_1_id = "need-hand-1"
    db.ngo_needs[need_1_id] = {
        "id": need_1_id,
        "receiver_id": "rp-1",
        "location_id": "loc-receiver-1",
        "required_quantity_kg": 20.0,
        "fulfilled_quantity_kg": 20.0,
        "required_by": required_by,
        "status": "MATCHED",
    }

    # Need 2
    need_2_id = "need-hand-2"
    db.ngo_needs[need_2_id] = {
        "id": need_2_id,
        "receiver_id": "rp-1",
        "location_id": "loc-receiver-1",
        "required_quantity_kg": 20.0,
        "fulfilled_quantity_kg": 20.0,
        "required_by": required_by,
        "status": "MATCHED",
    }

    alloc_1 = "alloc-h-1"
    db.donation_allocations[alloc_1] = {
        "id": alloc_1,
        "donation_id": donation_id,
        "need_id": need_1_id,
        "allocated_quantity_kg": 20.0,
        "status": "ACCEPTED",
    }

    alloc_2 = "alloc-h-2"
    db.donation_allocations[alloc_2] = {
        "id": alloc_2,
        "donation_id": donation_id,
        "need_id": need_2_id,
        "allocated_quantity_kg": 20.0,
        "status": "ACCEPTED",
    }

    # Create delivery
    deliv_res = client.post(
        "/api/v1/deliveries",
        headers={"Authorization": "Bearer token-user-donor-verified"},
        json={"donation_id": donation_id, "allocation_ids": [alloc_1, alloc_2]},
    )
    delivery_data = deliv_res.json()
    delivery_id = delivery_data["id"]

    # Create offers and accept by driver
    offers = client.post(
        f"/api/v1/deliveries/{delivery_id}/offers",
        headers={"Authorization": "Bearer token-user-donor-verified"},
    ).json()

    client.post(
        f"/api/v1/delivery-offers/{offers[0]['id']}/accept",
        headers={"Authorization": "Bearer token-user-driver-verified"},
    )

    # Transition driver to arrive-pickup
    client.post(
        f"/api/v1/deliveries/{delivery_id}/arrive-pickup",
        headers={"Authorization": "Bearer token-user-driver-verified"},
        json={"latitude": 28.6139, "longitude": 77.2090},
    )

    stops = client.get(
        f"/api/v1/deliveries/{delivery_id}",
        headers={"Authorization": "Bearer token-user-donor-verified"},
    ).json()["stops"]

    pickup_stop = next(s for s in stops if s["stop_type"] == "PICKUP")
    delivery_stops = [s for s in stops if s["stop_type"] == "DELIVERY"]

    return {
        "delivery_id": delivery_id,
        "donation_id": donation_id,
        "pickup_stop_id": pickup_stop["id"],
        "delivery_stops": delivery_stops,
    }


def test_pickup_otp_issuance_and_security(client: TestClient, mock_db: MockSupabaseClient):
    """Test secure pickup OTP generation, hashing, and authorization."""
    setup = setup_verified_delivery(client, mock_db)
    delivery_id = setup["delivery_id"]

    # 1. Driver or unauthorized user cannot generate pickup OTP
    unauth = client.post(
        f"/api/v1/deliveries/{delivery_id}/pickup-otp",
        headers={"Authorization": "Bearer token-user-driver-verified"},
    )
    assert unauth.status_code == 403

    # 2. Donor generates pickup OTP
    res = client.post(
        f"/api/v1/deliveries/{delivery_id}/pickup-otp",
        headers={"Authorization": "Bearer token-user-donor-verified"},
    )
    assert res.status_code == 201
    otp_data = res.json()
    assert "otp" in otp_data
    assert len(otp_data["otp"]) == 6
    plaintext_otp = otp_data["otp"]

    # 3. Verify OTP is NEVER stored plaintext in the database
    stored_records = list(mock_db.handoff_verifications.values())
    assert len(stored_records) > 0
    handoff_rec = stored_records[-1]
    assert handoff_rec["otp_hash"] != plaintext_otp
    assert "otp" not in handoff_rec
    assert handoff_rec["status"] == "PENDING"

    # 4. Reissuing invalidates the older pending OTP
    res2 = client.post(
        f"/api/v1/deliveries/{delivery_id}/pickup-otp",
        headers={"Authorization": "Bearer token-user-donor-verified"},
    )
    assert res2.status_code == 201
    assert handoff_rec["status"] == "EXPIRED"


def test_pickup_verification_workflow(client: TestClient, mock_db: MockSupabaseClient):
    """Test driver pickup verification with OTP, proximity check, and tamper seal creation."""
    setup = setup_verified_delivery(client, mock_db)
    delivery_id = setup["delivery_id"]

    # Generate OTP
    otp_res = client.post(
        f"/api/v1/deliveries/{delivery_id}/pickup-otp",
        headers={"Authorization": "Bearer token-user-donor-verified"},
    )
    otp = otp_res.json()["otp"]

    # 1. Invalid OTP rejection and attempts increment
    bad_otp_res = client.post(
        f"/api/v1/deliveries/{delivery_id}/verify-pickup",
        headers={"Authorization": "Bearer token-user-driver-verified"},
        json={"otp": "000000", "latitude": 28.6139, "longitude": 77.2090},
    )
    assert bad_otp_res.status_code == 409
    assert bad_otp_res.json()["error"]["code"] == "OTP_VERIFICATION_FAILED"

    # 2. Driver too far (>300m) rejected by GPS check
    far_res = client.post(
        f"/api/v1/deliveries/{delivery_id}/verify-pickup",
        headers={"Authorization": "Bearer token-user-driver-verified"},
        json={"otp": otp, "latitude": 28.4595, "longitude": 77.0266},  # Gurgaon 50km away
    )
    assert far_res.status_code == 409
    assert far_res.json()["error"]["code"] == "PROXIMITY_CHECK_FAILED"

    # 3. Successful verification
    good_res = client.post(
        f"/api/v1/deliveries/{delivery_id}/verify-pickup",
        headers={"Authorization": "Bearer token-user-driver-verified"},
        json={"otp": otp, "latitude": 28.6139, "longitude": 77.2090, "accuracy_meters": 4.5},
    )
    assert good_res.status_code == 200
    deliv_data = good_res.json()
    assert deliv_data["status"] == "PICKED_UP"
    assert deliv_data["picked_up_at"] is not None

    # Check tamper seal created
    seals = list(mock_db.package_seals.values())
    assert len(seals) > 0
    seal = seals[-1]
    assert seal["seal_id"].startswith("ANNA-")
    assert seal["pickup_status"] == "INTACT"

    # 4. Single-use check: reused OTP must fail
    reuse_res = client.post(
        f"/api/v1/deliveries/{delivery_id}/verify-pickup",
        headers={"Authorization": "Bearer token-user-driver-verified"},
        json={"otp": otp, "latitude": 28.6139, "longitude": 77.2090},
    )
    assert reuse_res.status_code == 409


def test_pickup_evidence_upload(client: TestClient, mock_db: MockSupabaseClient):
    """Test driver uploading package and seal photos upon pickup."""
    setup = setup_verified_delivery(client, mock_db)
    delivery_id = setup["delivery_id"]

    evidence_res = client.post(
        f"/api/v1/deliveries/{delivery_id}/pickup-evidence",
        headers={"Authorization": "Bearer token-user-driver-verified"},
        json={
            "package_image": "data:image/jpeg;base64,/9j/4AAQSkZJRg==",
            "seal_image": "data:image/jpeg;base64,/9j/4AAQSkZJRg==",
            "latitude": 28.6139,
            "longitude": 77.2090,
        },
    )
    assert evidence_res.status_code == 201
    items = evidence_res.json()
    assert len(items) == 2
    types = [i["evidence_type"] for i in items]
    assert "PACKAGE_PHOTO" in types
    assert "SEAL_PHOTO" in types


def test_delivery_stop_otp_and_completion(client: TestClient, mock_db: MockSupabaseClient):
    """Test multi-stop delivery verification, seal inspection, and final DELIVERED state."""
    setup = setup_verified_delivery(client, mock_db)
    delivery_id = setup["delivery_id"]
    delivery_stops = setup["delivery_stops"]
    stop_1_id = delivery_stops[0]["id"]
    stop_2_id = delivery_stops[1]["id"]

    # Complete pickup first
    p_otp = client.post(
        f"/api/v1/deliveries/{delivery_id}/pickup-otp",
        headers={"Authorization": "Bearer token-user-donor-verified"},
    ).json()["otp"]
    client.post(
        f"/api/v1/deliveries/{delivery_id}/verify-pickup",
        headers={"Authorization": "Bearer token-user-driver-verified"},
        json={"otp": p_otp, "latitude": 28.6139, "longitude": 77.2090},
    )

    # Start transit to stop 1
    client.post(
        f"/api/v1/deliveries/{delivery_id}/start-transit",
        headers={"Authorization": "Bearer token-user-driver-verified"},
    )
    client.post(
        f"/api/v1/deliveries/{delivery_id}/arrive-stop",
        headers={"Authorization": "Bearer token-user-driver-verified"},
        json={"latitude": 28.5672, "longitude": 77.1982},
    )

    # Receiver generates delivery OTP for Stop 1
    d_otp_1 = client.post(
        f"/api/v1/deliveries/{delivery_id}/stops/{stop_1_id}/delivery-otp",
        headers={"Authorization": "Bearer token-user-receiver-verified"},
    ).json()["otp"]

    # Verify Stop 1 with INTACT seal
    stop1_res = client.post(
        f"/api/v1/deliveries/{delivery_id}/stops/{stop_1_id}/verify-delivery?seal_condition=INTACT",
        headers={"Authorization": "Bearer token-user-driver-verified"},
        json={"otp": d_otp_1, "latitude": 28.5672, "longitude": 77.1982},
    )
    assert stop1_res.status_code == 200
    data_1 = stop1_res.json()
    # Still 1 stop remaining, so delivery should transition to IN_TRANSIT
    assert data_1["status"] == "IN_TRANSIT"

    # Arrive at Stop 2
    client.post(
        f"/api/v1/deliveries/{delivery_id}/arrive-stop",
        headers={"Authorization": "Bearer token-user-driver-verified"},
        json={"latitude": 28.5672, "longitude": 77.1982},
    )

    # Receiver generates OTP for Stop 2
    d_otp_2 = client.post(
        f"/api/v1/deliveries/{delivery_id}/stops/{stop_2_id}/delivery-otp",
        headers={"Authorization": "Bearer token-user-receiver-verified"},
    ).json()["otp"]

    # Verify Stop 2
    stop2_res = client.post(
        f"/api/v1/deliveries/{delivery_id}/stops/{stop_2_id}/verify-delivery?seal_condition=INTACT",
        headers={"Authorization": "Bearer token-user-driver-verified"},
        json={"otp": d_otp_2, "latitude": 28.5672, "longitude": 77.1982},
    )
    assert stop2_res.status_code == 200
    final_data = stop2_res.json()
    # All delivery stops completed -> final mission DELIVERED!
    assert final_data["status"] == "DELIVERED"
    assert final_data["completed_at"] is not None

    # Driver should be freed back to AVAILABLE
    drp = mock_db.driver_profiles["user-driver-verified"]
    assert drp["availability_status"] == "AVAILABLE"


def test_seal_discrepancy_and_manual_review(client: TestClient, mock_db: MockSupabaseClient):
    """Test seal discrepancy recording and operational manual review flow."""
    setup = setup_verified_delivery(client, mock_db)
    delivery_id = setup["delivery_id"]
    stop_id = setup["delivery_stops"][0]["id"]

    # Complete pickup
    p_otp = client.post(
        f"/api/v1/deliveries/{delivery_id}/pickup-otp",
        headers={"Authorization": "Bearer token-user-donor-verified"},
    ).json()["otp"]
    client.post(
        f"/api/v1/deliveries/{delivery_id}/verify-pickup",
        headers={"Authorization": "Bearer token-user-driver-verified"},
        json={"otp": p_otp, "latitude": 28.6139, "longitude": 77.2090},
    )
    # Upload pickup evidence
    client.post(
        f"/api/v1/deliveries/{delivery_id}/pickup-evidence",
        headers={"Authorization": "Bearer token-user-driver-verified"},
        json={"package_image": "pkg-pickup.jpg", "seal_image": "seal-pickup.jpg"},
    )

    client.post(
        f"/api/v1/deliveries/{delivery_id}/start-transit",
        headers={"Authorization": "Bearer token-user-driver-verified"},
    )
    client.post(
        f"/api/v1/deliveries/{delivery_id}/arrive-stop",
        headers={"Authorization": "Bearer token-user-driver-verified"},
        json={"latitude": 28.5672, "longitude": 77.1982},
    )

    # Upload delivery evidence with BROKEN seal observation
    client.post(
        f"/api/v1/deliveries/{delivery_id}/stops/{stop_id}/delivery-evidence",
        headers={"Authorization": "Bearer token-user-driver-verified"},
        json={
            "package_image": "pkg-delivery.jpg",
            "seal_image": "seal-delivery.jpg",
            "seal_condition": "BROKEN",
        },
    )

    # Check food_integrity_checks record created
    integrity_records = list(mock_db.food_integrity_checks.values())
    assert len(integrity_records) > 0
    check = integrity_records[-1]
    assert check["delivery_id"] == delivery_id
    assert check["delivery_seal_status"] == "BROKEN"
    assert check["manual_review_status"] == "REQUIRES_ACTION"

    # Admin reviews and clears check
    admin_reviews = client.get(
        "/api/v1/integrity/reviews?status=REQUIRES_ACTION",
        headers={"Authorization": "Bearer token-user-admin"},
    )
    assert admin_reviews.status_code == 200
    assert len(admin_reviews.json()) > 0

    clear_res = client.post(
        f"/api/v1/integrity/{check['id']}/review",
        headers={"Authorization": "Bearer token-user-admin"},
        json={"status": "CLEARED", "notes": "Packaging verified with donor and receiver by phone. Cleared."},
    )
    assert clear_res.status_code == 200
    assert clear_res.json()["manual_review_status"] == "CLEARED"
