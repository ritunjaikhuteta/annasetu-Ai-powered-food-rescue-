"""Tests for Deterministic Rescue Matching Engine."""

from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient


def get_offsets(start_h: int = 1, end_h: int = 6):
    now = datetime.now(timezone.utc)
    start = (now + timedelta(hours=start_h)).isoformat()
    end = (now + timedelta(hours=end_h)).isoformat()
    prep = (now - timedelta(hours=1)).isoformat()
    return prep, start, end


def test_matching_flow_and_eligibility_filters(client: TestClient):
    prep, avail, deadline = get_offsets(start_h=1, end_h=6)

    # 1. Create and Activate an eligible Need
    need_payload = {
        "meal_period": "DINNER",
        "diet_type": "VEGETARIAN",
        "food_category_id": "cat-cooked-meals",
        "required_quantity_kg": 30.0,
        "minimum_quantity_kg": 10.0,
        "receiving_capacity_kg": 40.0,
        "required_by": (datetime.now(timezone.utc) + timedelta(hours=7)).isoformat(),
        "location_id": "loc-receiver-1",
    }
    n_res = client.post(
        "/api/v1/needs",
        headers={"Authorization": "Bearer token-user-receiver-verified"},
        json=need_payload,
    )
    assert n_res.status_code == 201
    need_id = n_res.json()["id"]

    client.post(
        f"/api/v1/needs/{need_id}/activate",
        headers={"Authorization": "Bearer token-user-receiver-verified"},
    )

    # 2. Create and Post a compatible Donation
    don_payload = {
        "diet_type": "VEGETARIAN",
        "food_category_id": "cat-cooked-meals",
        "declared_quantity_kg": 40.0,
        "preparation_at": prep,
        "available_from": avail,
        "rescue_deadline": deadline,
        "storage_condition": "refrigerated",
        "packaging_type": "Sealed trays",
        "raw_description": "Cooked vegetarian meals",
        "pickup_location_id": "loc-donor-1",
    }
    d_res = client.post(
        "/api/v1/donations",
        headers={"Authorization": "Bearer token-user-donor-verified"},
        json=don_payload,
    )
    assert d_res.status_code == 201
    donation_id = d_res.json()["id"]

    client.post(
        f"/api/v1/donations/{donation_id}/post",
        headers={"Authorization": "Bearer token-user-donor-verified"},
    )

    # 3. Generate matches
    match_res = client.post(
        f"/api/v1/donations/{donation_id}/generate-matches",
        headers={"Authorization": "Bearer token-user-donor-verified"},
    )
    assert match_res.status_code == 200
    matches = match_res.json()
    assert len(matches) == 1
    match = matches[0]

    assert match["donation_id"] == donation_id
    assert match["need_id"] == need_id
    assert match["fulfillable_quantity_kg"] == 30.0  # bottlenecked by need required quantity
    assert match["priority_score"] > 0
    assert match["priority_label"] in ("HIGH", "MEDIUM", "LOW")
    assert "rescue priority" in match["explanation"]
    assert "priority_breakdown" in match

    # 4. Duplicate match prevention: running generate-matches again updates rather than duplicating
    rematch_res = client.post(
        f"/api/v1/donations/{donation_id}/generate-matches",
        headers={"Authorization": "Bearer token-user-donor-verified"},
    )
    assert rematch_res.status_code == 200
    assert len(rematch_res.json()) == 1


def test_inactive_draft_need_excluded_from_matching(client: TestClient):
    prep, avail, deadline = get_offsets(start_h=1, end_h=6)

    # Need kept in DRAFT status
    need_payload = {
        "meal_period": "DINNER",
        "diet_type": "VEGETARIAN",
        "food_category_id": "cat-cooked-meals",
        "required_quantity_kg": 20.0,
        "minimum_quantity_kg": 5.0,
        "receiving_capacity_kg": 30.0,
        "required_by": (datetime.now(timezone.utc) + timedelta(hours=8)).isoformat(),
        "location_id": "loc-receiver-1",
    }
    client.post(
        "/api/v1/needs",
        headers={"Authorization": "Bearer token-user-receiver-verified"},
        json=need_payload,
    )

    don_payload = {
        "diet_type": "VEGETARIAN",
        "food_category_id": "cat-cooked-meals",
        "declared_quantity_kg": 25.0,
        "preparation_at": prep,
        "available_from": avail,
        "rescue_deadline": deadline,
        "packaging_type": "Sealed trays",
        "raw_description": "Vegetarian buffet surplus",
        "pickup_location_id": "loc-donor-1",
    }
    d_res = client.post(
        "/api/v1/donations",
        headers={"Authorization": "Bearer token-user-donor-verified"},
        json=don_payload,
    )
    donation_id = d_res.json()["id"]
    client.post(
        f"/api/v1/donations/{donation_id}/post",
        headers={"Authorization": "Bearer token-user-donor-verified"},
    )

    match_res = client.post(
        f"/api/v1/donations/{donation_id}/generate-matches",
        headers={"Authorization": "Bearer token-user-donor-verified"},
    )
    # Draft need must be excluded
    matches = [m for m in match_res.json() if m["donation_id"] == donation_id]
    assert len(matches) == 0


def test_incompatible_diet_excluded(client: TestClient):
    prep, avail, deadline = get_offsets(start_h=1, end_h=6)

    # Vegetarian need
    n_res = client.post(
        "/api/v1/needs",
        headers={"Authorization": "Bearer token-user-receiver-verified"},
        json={
            "meal_period": "LUNCH",
            "diet_type": "VEGETARIAN",
            "food_category_id": "cat-nonveg-chicken",
            "required_quantity_kg": 20.0,
            "minimum_quantity_kg": 5.0,
            "receiving_capacity_kg": 30.0,
            "required_by": (datetime.now(timezone.utc) + timedelta(hours=8)).isoformat(),
            "location_id": "loc-receiver-1",
        },
    )
    need_id = n_res.json()["id"]
    client.post(
        f"/api/v1/needs/{need_id}/activate",
        headers={"Authorization": "Bearer token-user-receiver-verified"},
    )

    # Non-vegetarian donation
    d_res = client.post(
        "/api/v1/donations",
        headers={"Authorization": "Bearer token-user-donor-verified"},
        json={
            "diet_type": "NON_VEGETARIAN",
            "food_category_id": "cat-nonveg-chicken",
            "declared_quantity_kg": 20.0,
            "preparation_at": prep,
            "available_from": avail,
            "rescue_deadline": deadline,
            "packaging_type": "Sealed boxes",
            "raw_description": "Non-vegetarian chicken curry",
            "pickup_location_id": "loc-donor-1",
        },
    )
    don_id = d_res.json()["id"]
    client.post(f"/api/v1/donations/{don_id}/post", headers={"Authorization": "Bearer token-user-donor-verified"})

    match_res = client.post(
        f"/api/v1/donations/{don_id}/generate-matches",
        headers={"Authorization": "Bearer token-user-donor-verified"},
    )
    matched_ids = [m["need_id"] for m in match_res.json()]
    assert need_id not in matched_ids
