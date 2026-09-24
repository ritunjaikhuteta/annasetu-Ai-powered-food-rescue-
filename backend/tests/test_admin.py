"""Unit and Integration Tests for Phase 17: AnnaSetu Admin + Operations Command Center."""

from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient
from tests.conftest import MockSupabaseClient


# =============================================================================
# 1. ADMIN AUTHORIZATION SECURITY
# =============================================================================

def test_non_admin_rejected_from_admin_endpoints(client: TestClient):
    """Non-admin roles (DONOR, RECEIVER, DRIVER) must receive HTTP 403 Forbidden."""
    donor_headers = {"Authorization": "Bearer token-user-donor-verified"}
    receiver_headers = {"Authorization": "Bearer token-user-receiver-verified"}
    driver_headers = {"Authorization": "Bearer token-user-driver-verified"}

    endpoints = [
        ("GET", "/api/v1/admin/overview"),
        ("GET", "/api/v1/admin/verifications"),
        ("GET", "/api/v1/admin/operations/active"),
        ("GET", "/api/v1/admin/operations/exceptions"),
        ("GET", "/api/v1/admin/users"),
        ("GET", "/api/v1/admin/financial/exceptions"),
        ("GET", "/api/v1/admin/analytics/impact"),
        ("GET", "/api/v1/admin/audit-logs"),
    ]

    for method, ep in endpoints:
        for headers in (donor_headers, receiver_headers, driver_headers):
            if method == "GET":
                res = client.get(ep, headers=headers)
            else:
                res = client.post(ep, headers=headers, json={})
            assert res.status_code == 403, f"Expected 403 on {ep} for non-admin, got {res.status_code}"


def test_admin_access_accepted(client: TestClient):
    """Verified ADMIN user receives 200 OK on admin endpoints."""
    admin_headers = {"Authorization": "Bearer token-user-admin"}
    res = client.get("/api/v1/admin/overview", headers=admin_headers)
    assert res.status_code == 200
    data = res.json()
    assert "operational_health" in data
    assert "active_donors" in data


# =============================================================================
# 2. OVERVIEW & OPERATIONAL HEALTH
# =============================================================================

def test_admin_overview_metrics(client: TestClient, mock_db: MockSupabaseClient):
    """Overview aggregates metrics from real database records."""
    admin_headers = {"Authorization": "Bearer token-user-admin"}
    res = client.get("/api/v1/admin/overview", headers=admin_headers)
    assert res.status_code == 200
    data = res.json()

    assert data["active_donors"] >= 1
    assert data["active_receivers"] >= 1
    assert data["verified_drivers"] >= 1
    assert data["operational_health"]["database"] == "AVAILABLE"


# =============================================================================
# 3. VERIFICATION QUEUE & HUMAN APPROVAL RULES
# =============================================================================

@pytest.mark.anyio
async def test_verification_queue_and_approval_flow(
    client: TestClient,
    mock_db: MockSupabaseClient,
):
    """Admin inspects verification case and approves it, updating record and profile."""
    admin_headers = {"Authorization": "Bearer token-user-admin"}

    # Seed pending verification record for pending donor
    mock_db.verification_records["verif-test-1"] = {
        "id": "verif-test-1",
        "user_id": "user-donor-pending",
        "role": "DONOR",
        "verification_type": "FSSAI_REGISTRATION",
        "status": "PENDING",
        "created_at": "2026-09-24T10:00:00Z",
    }
    mock_db.verification_documents["vdoc-test-1"] = {
        "id": "vdoc-test-1",
        "verification_id": "verif-test-1",
        "user_id": "user-donor-pending",
        "document_type": "FSSAI_LICENSE",
        "status": "PENDING",
    }

    # 1. List queue
    list_res = client.get("/api/v1/admin/verifications", headers=admin_headers)
    assert list_res.status_code == 200
    q_data = list_res.json()
    assert q_data["total"] >= 1

    # 2. Detail view
    detail_res = client.get("/api/v1/admin/verifications/verif-test-1", headers=admin_headers)
    assert detail_res.status_code == 200
    d_data = detail_res.json()
    assert d_data["user_id"] == "user-donor-pending"
    assert len(d_data["documents"]) == 1

    # 3. Approve verification
    approve_res = client.post(
        "/api/v1/admin/verifications/verif-test-1/approve",
        headers=admin_headers,
        json={"review_notes": "All documents verified against official registry."},
    )
    assert approve_res.status_code == 200
    app_data = approve_res.json()
    assert app_data["status"] == "VERIFIED"
    assert app_data["verified_by"] == "user-admin"

    # Verify donor profile was updated to VERIFIED
    dp = mock_db.donor_profiles["user-donor-pending"]
    assert dp["verification_status"] == "VERIFIED"


@pytest.mark.anyio
async def test_verification_rejection_requires_reason(
    client: TestClient,
    mock_db: MockSupabaseClient,
):
    """Rejection requires a documented reason and sets status to REJECTED."""
    admin_headers = {"Authorization": "Bearer token-user-admin"}

    mock_db.verification_records["verif-rej-1"] = {
        "id": "verif-rej-1",
        "user_id": "user-donor-pending",
        "role": "DONOR",
        "status": "PENDING",
    }

    # Missing rejection reason fails validation
    bad_res = client.post(
        "/api/v1/admin/verifications/verif-rej-1/reject",
        headers=admin_headers,
        json={"rejection_reason": "ab"},  # min 3 chars
    )
    assert bad_res.status_code == 422

    # Valid rejection
    res = client.post(
        "/api/v1/admin/verifications/verif-rej-1/reject",
        headers=admin_headers,
        json={"rejection_reason": "FSSAI certificate was expired and illegible."},
    )
    assert res.status_code == 200
    assert res.json()["status"] == "REJECTED"
    assert res.json()["rejection_reason"] == "FSSAI certificate was expired and illegible."


# =============================================================================
# 4. USER DIRECTORY & ACTIONS
# =============================================================================

def test_user_directory_and_activation(client: TestClient, mock_db: MockSupabaseClient):
    """Admin searches user directory and toggles user active status."""
    admin_headers = {"Authorization": "Bearer token-user-admin"}

    # Search user
    res = client.get("/api/v1/admin/users?search=Chef", headers=admin_headers)
    assert res.status_code == 200
    data = res.json()
    assert data["total"] >= 1
    assert data["items"][0]["full_name"] == "Verified Donor Chef"

    # Deactivate user
    deact_res = client.post(
        "/api/v1/admin/users/user-donor-verified/deactivate",
        headers=admin_headers,
        json={"reason": "Temporary suspension for audit inquiry."},
    )
    assert deact_res.status_code == 200
    assert mock_db.profiles["user-donor-verified"]["is_active"] is False

    # Reactivate user
    act_res = client.post(
        "/api/v1/admin/users/user-donor-verified/activate",
        headers=admin_headers,
        json={"reason": "Audit inquiry resolved."},
    )
    assert act_res.status_code == 200
    assert mock_db.profiles["user-donor-verified"]["is_active"] is True


# =============================================================================
# 5. LIVE RESCUE OPERATIONS, EXCEPTIONS & REASSIGNMENT
# =============================================================================

@pytest.mark.anyio
async def test_live_operations_and_exceptions(
    client: TestClient,
    mock_db: MockSupabaseClient,
):
    """Admin views active deliveries and exceptions queue."""
    admin_headers = {"Authorization": "Bearer token-user-admin"}

    mock_db.deliveries["del-live-1"] = {
        "id": "del-live-1",
        "donation_id": "don-1",
        "driver_id": "user-driver-verified",
        "status": "IN_TRANSIT",
        "pickup_location_id": "loc-donor-1",
    }
    mock_db.deliveries["del-exc-1"] = {
        "id": "del-exc-1",
        "donation_id": "don-1",
        "driver_id": "user-driver-verified",
        "status": "REASSIGNMENT_REQUIRED",
    }

    # Active deliveries
    live_res = client.get("/api/v1/admin/operations/active", headers=admin_headers)
    assert live_res.status_code == 200
    live_items = live_res.json()
    assert any(d["delivery_id"] == "del-live-1" for d in live_items)

    # Exceptions
    exc_res = client.get("/api/v1/admin/operations/exceptions", headers=admin_headers)
    assert exc_res.status_code == 200
    exc_items = exc_res.json()
    assert any(e["delivery_id"] == "del-exc-1" for e in exc_items)


@pytest.mark.anyio
async def test_delivery_reassignment(
    client: TestClient,
    mock_db: MockSupabaseClient,
):
    """Admin reassigns delivery to a verified, available driver."""
    admin_headers = {"Authorization": "Bearer token-user-admin"}

    # Seed target new driver
    mock_db.profiles["user-driver-2"] = {
        "id": "user-driver-2",
        "full_name": "Second Driver",
        "role": "DRIVER",
        "is_active": True,
    }
    mock_db.driver_profiles["user-driver-2"] = {
        "id": "drp-2",
        "user_id": "user-driver-2",
        "vehicle_type": "van",
        "vehicle_number": "DL-01-XY-5678",
        "verification_status": "VERIFIED",
        "is_online": True,
        "availability_status": "AVAILABLE",
    }

    mock_db.deliveries["del-reassign-target"] = {
        "id": "del-reassign-target",
        "status": "REASSIGNMENT_REQUIRED",
        "driver_id": "user-driver-verified",
    }

    res = client.post(
        "/api/v1/admin/deliveries/del-reassign-target/reassign",
        headers=admin_headers,
        json={"new_driver_id": "user-driver-2", "reason": "First driver broke down."},
    )
    assert res.status_code == 200
    updated_del = mock_db.deliveries["del-reassign-target"]
    assert updated_del["driver_id"] == "user-driver-2"
    assert updated_del["status"] == "ACCEPTED"


# =============================================================================
# 6. INTEGRITY REVIEWS
# =============================================================================

@pytest.mark.anyio
async def test_admin_integrity_review_flow(
    client: TestClient,
    mock_db: MockSupabaseClient,
):
    """Admin reviews food integrity check and clears discrepancy."""
    admin_headers = {"Authorization": "Bearer token-user-admin"}

    mock_db.food_integrity_checks["chk-adm-1"] = {
        "id": "chk-adm-1",
        "delivery_id": "del-live-1",
        "check_type": "PACKAGE_VISUAL_CONSISTENCY",
        "tampering_signal": True,
        "manual_review_status": "REQUIRES_ACTION",
        "pickup_seal_status": "INTACT",
        "delivery_seal_status": "BROKEN",
        "ai_integrity_score": 65.0,
    }

    # List reviews
    list_res = client.get("/api/v1/admin/integrity/reviews", headers=admin_headers)
    assert list_res.status_code == 200
    assert len(list_res.json()) >= 1

    # Detail view
    det_res = client.get("/api/v1/admin/integrity/chk-adm-1", headers=admin_headers)
    assert det_res.status_code == 200
    assert det_res.json()["tampering_signal"] is True

    # Submit review outcome
    sub_res = client.post(
        "/api/v1/admin/integrity/chk-adm-1/review",
        headers=admin_headers,
        json={"status": "CLEARED", "notes": "Recipient verified seal broke during unloading; food intact."},
    )
    assert sub_res.status_code == 200
    assert sub_res.json()["manual_review_status"] == "CLEARED"


# =============================================================================
# 7. FINANCIAL EXCEPTIONS & ADJUSTMENTS
# =============================================================================

@pytest.mark.anyio
async def test_admin_financial_exceptions_and_adjustment(
    client: TestClient,
    mock_db: MockSupabaseClient,
):
    """Admin inspects financial exceptions and applies a controlled ledger adjustment."""
    admin_headers = {"Authorization": "Bearer token-user-admin"}

    mock_db.wallets["w-admin-test"] = {
        "id": "w-admin-test",
        "user_id": "user-receiver-verified",
        "balance": 1500.0,
    }
    mock_db.transactions["tx-failed-1"] = {
        "id": "tx-failed-1",
        "wallet_id": "w-admin-test",
        "type": "DELIVERY_PAYMENT",
        "amount": 250.0,
        "status": "FAILED",
        "created_at": "2026-09-24T12:00:00Z",
    }

    # List exceptions
    exc_res = client.get("/api/v1/admin/financial/exceptions", headers=admin_headers)
    assert exc_res.status_code == 200
    items = exc_res.json()
    assert any(i["related_entity_id"] == "tx-failed-1" for i in items)

    # Controlled adjustment: Credit INR 100
    adj_res = client.post(
        "/api/v1/admin/financial/adjust",
        headers=admin_headers,
        json={
            "wallet_id": "w-admin-test",
            "amount": 100.0,
            "adjustment_type": "CREDIT",
            "reason": "Administrative fee waiver compensation.",
            "original_reference_id": "tx-failed-1",
        },
    )
    assert adj_res.status_code == 200
    adj_data = adj_res.json()
    assert adj_data["type"] == "ADJUSTMENT"
    assert adj_data["amount"] == 100.0
    assert adj_data["balance_after"] == 1600.0

    # Ensure wallet was updated
    assert mock_db.wallets["w-admin-test"]["balance"] == 1600.0


# =============================================================================
# 8. AUDIT LOGS & ANALYTICS
# =============================================================================

def test_admin_audit_logs_pagination(client: TestClient, mock_db: MockSupabaseClient):
    """Audit logs are paginated and searchable."""
    admin_headers = {"Authorization": "Bearer token-user-admin"}

    res = client.get("/api/v1/admin/audit-logs?page=1&page_size=10", headers=admin_headers)
    assert res.status_code == 200
    data = res.json()
    assert "items" in data
    assert "total" in data
    assert data["page_size"] == 10


def test_admin_analytics_periods(client: TestClient, mock_db: MockSupabaseClient):
    """Analytics endpoints support period filters."""
    admin_headers = {"Authorization": "Bearer token-user-admin"}

    for period in ("today", "7d", "30d", "90d"):
        res = client.get(f"/api/v1/admin/analytics/impact?period={period}", headers=admin_headers)
        assert res.status_code == 200
        assert res.json()["period"] == period

        ops_res = client.get(f"/api/v1/admin/analytics/operations?period={period}", headers=admin_headers)
        assert ops_res.status_code == 200
        assert ops_res.json()["period"] == period

        fin_res = client.get(f"/api/v1/admin/analytics/financial?period={period}", headers=admin_headers)
        assert fin_res.status_code == 200
        assert fin_res.json()["period"] == period
