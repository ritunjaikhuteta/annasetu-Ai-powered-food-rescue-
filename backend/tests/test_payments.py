"""Phase 15 Payments, Wallet, and Subscriptions Test Suite."""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Dict
import pytest
from fastapi.testclient import TestClient
from tests.conftest import MockSupabaseClient


def setup_pricing_delivery(client: TestClient, db: MockSupabaseClient) -> Dict[str, Any]:
    """Helper to setup a delivery for pricing and financial tests."""
    now = datetime.now(timezone.utc)
    donation_id = "don-pay-1"
    db.donations[donation_id] = {
        "id": donation_id,
        "donor_id": "user-donor-verified",
        "title": "Paneer Butter Masala",
        "pickup_location_id": "loc-donor-1",
        "total_quantity_kg": 30.0,
        "available_quantity_kg": 0.0,
        "rescue_deadline": (now + timedelta(hours=4)).isoformat(),
        "status": "ALLOCATED",
    }

    need_id = "need-pay-1"
    db.ngo_needs[need_id] = {
        "id": need_id,
        "receiver_id": "rp-1",
        "location_id": "loc-receiver-1",
        "required_quantity_kg": 30.0,
        "fulfilled_quantity_kg": 30.0,
        "required_by": (now + timedelta(hours=3)).isoformat(),
        "status": "MATCHED",
    }

    alloc_id = "alloc-pay-1"
    db.donation_allocations[alloc_id] = {
        "id": alloc_id,
        "donation_id": donation_id,
        "need_id": need_id,
        "allocated_quantity_kg": 30.0,
        "status": "ACCEPTED",
    }

    deliv_res = client.post(
        "/api/v1/deliveries",
        headers={"Authorization": "Bearer token-user-donor-verified"},
        json={"donation_id": donation_id, "allocation_ids": [alloc_id]},
    )
    delivery = deliv_res.json()
    return {"delivery_id": delivery["id"], "donation_id": donation_id}


def test_pricing_calculation_and_snapshot(client: TestClient, mock_db: MockSupabaseClient):
    """Test Decimal-safe delivery pricing calculation with 12% platform fee and snapshotting."""
    setup = setup_pricing_delivery(client, mock_db)
    delivery_id = setup["delivery_id"]

    # Seed custom pricing rule: Base 50, Per km 15, Per min 2, Stop 25, Fee 12%
    mock_db.pricing_rules["rule-1"] = {
        "id": "rule-1",
        "base_fare": 50.00,
        "per_km_rate": 15.00,
        "per_minute_rate": 2.00,
        "stop_fee": 25.00,
        "platform_fee_percent": 12.00,
        "is_active": True,
    }

    res = client.get(
        f"/api/v1/pricing/delivery/{delivery_id}",
        headers={"Authorization": "Bearer token-user-receiver-verified"},
    )
    assert res.status_code == 200
    data = res.json()

    # Verify components are Decimals formatted to 2 places
    assert Decimal(str(data["base_fare"])) == Decimal("50.00")
    assert Decimal(str(data["platform_fee_percent"])) == Decimal("12.00")

    deliv_charge = Decimal(str(data["delivery_charge"]))
    platform_fee = Decimal(str(data["platform_fee"]))
    ngo_total = Decimal(str(data["ngo_total"]))
    driver_payout = Decimal(str(data["driver_payout"]))

    # Formula: platform_fee = round(deliv_charge * 0.12, 2)
    expected_fee = (deliv_charge * Decimal("0.12")).quantize(Decimal("0.01"))
    assert platform_fee == expected_fee
    assert ngo_total == deliv_charge + platform_fee
    assert driver_payout >= Decimal("80.00")  # Minimum driver payout

    # Verify snapshot was stored in delivery record
    stored_deliv = mock_db.deliveries[delivery_id]
    assert stored_deliv.get("delivery_charge") is not None
    assert stored_deliv.get("platform_fee") is not None
    assert stored_deliv.get("ngo_total") is not None


def test_ngo_wallet_retrieval_and_topup(client: TestClient, mock_db: MockSupabaseClient):
    """Test NGO wallet initialization, available balance calculation, and top-up."""
    # 1. Initial wallet fetch -> ₹0 balance
    res = client.get(
        "/api/v1/wallet",
        headers={"Authorization": "Bearer token-user-receiver-verified"},
    )
    assert res.status_code == 200
    wallet = res.json()
    assert Decimal(str(wallet["balance"])) == Decimal("0.00")
    assert Decimal(str(wallet["reserved_balance"])) == Decimal("0.00")
    assert Decimal(str(wallet["available_balance"])) == Decimal("0.00")

    # 2. Top-up ₹500
    topup_res = client.post(
        "/api/v1/wallet/top-up",
        headers={"Authorization": "Bearer token-user-receiver-verified"},
        json={"amount": 500.00, "idempotency_key": "topup-test-1"},
    )
    assert topup_res.status_code == 200
    topup_data = topup_res.json()
    assert Decimal(str(topup_data["amount"])) == Decimal("500.00")
    assert Decimal(str(topup_data["new_balance"])) == Decimal("500.00")

    # 3. Idempotent top-up retry with same key does not double-credit
    retry_res = client.post(
        "/api/v1/wallet/top-up",
        headers={"Authorization": "Bearer token-user-receiver-verified"},
        json={"amount": 500.00, "idempotency_key": "topup-test-1"},
    )
    assert retry_res.status_code == 200
    assert Decimal(str(retry_res.json()["new_balance"])) == Decimal("500.00")

    # 4. Check transactions ledger
    tx_res = client.get(
        "/api/v1/wallet/transactions",
        headers={"Authorization": "Bearer token-user-receiver-verified"},
    )
    assert tx_res.status_code == 200
    txs = tx_res.json()
    assert len(txs) == 1
    assert txs[0]["type"] == "TOP_UP"
    assert Decimal(str(txs[0]["amount"])) == Decimal("500.00")


def test_wallet_reservation_and_insufficient_funds(client: TestClient, mock_db: MockSupabaseClient):
    """Test fund reservation against available balance and rejection on insufficient funds."""
    setup = setup_pricing_delivery(client, mock_db)
    delivery_id = setup["delivery_id"]

    # 1. Attempt reservation without topping up -> Must be 409 INSUFFICIENT_FUNDS
    res_fail = client.post(
        f"/api/v1/deliveries/{delivery_id}/reserve",
        headers={"Authorization": "Bearer token-user-receiver-verified"},
    )
    assert res_fail.status_code == 409
    assert res_fail.json()["error"]["code"] == "INSUFFICIENT_FUNDS"

    # 2. Top-up ₹1,000
    client.post(
        "/api/v1/wallet/top-up",
        headers={"Authorization": "Bearer token-user-receiver-verified"},
        json={"amount": 1000.00},
    )

    # 3. Reservation should now succeed
    res_success = client.post(
        f"/api/v1/deliveries/{delivery_id}/reserve",
        headers={"Authorization": "Bearer token-user-receiver-verified"},
    )
    assert res_success.status_code == 200
    res_data = res_success.json()
    assert res_data["status"] == "ACTIVE"
    reserved_amount = Decimal(str(res_data["reserved_amount"]))
    assert reserved_amount > Decimal("0.00")

    # 4. Verify wallet available balance was reduced
    wallet = client.get(
        "/api/v1/wallet",
        headers={"Authorization": "Bearer token-user-receiver-verified"},
    ).json()
    assert Decimal(str(wallet["reserved_balance"])) == reserved_amount
    assert Decimal(str(wallet["available_balance"])) == Decimal("1000.00") - reserved_amount


def test_delivery_settlement_and_driver_payout(client: TestClient, mock_db: MockSupabaseClient):
    """Test atomic final settlement, NGO payment capture, and driver payout."""
    setup = setup_pricing_delivery(client, mock_db)
    delivery_id = setup["delivery_id"]

    # Top-up NGO wallet
    client.post(
        "/api/v1/wallet/top-up",
        headers={"Authorization": "Bearer token-user-receiver-verified"},
        json={"amount": 1000.00},
    )
    # Reserve funds
    client.post(
        f"/api/v1/deliveries/{delivery_id}/reserve",
        headers={"Authorization": "Bearer token-user-receiver-verified"},
    )

    # 1. Attempt settlement while NOT delivered -> Must fail with 409
    fail_settle = client.post(
        f"/api/v1/deliveries/{delivery_id}/settle",
        headers={"Authorization": "Bearer token-user-driver-verified"},
    )
    assert fail_settle.status_code == 409

    # Advance delivery to DELIVERED and assign driver drp-1
    mock_db.deliveries[delivery_id].update({
        "status": "DELIVERED",
        "driver_id": "drp-1",
    })

    # 2. Settle delivery
    settle_res = client.post(
        f"/api/v1/deliveries/{delivery_id}/settle",
        headers={"Authorization": "Bearer token-user-driver-verified"},
    )
    assert settle_res.status_code == 200
    settle_data = settle_res.json()
    assert settle_data["status"] == "SETTLED"

    # 3. Check Driver wallet received payout
    driver_wallet = client.get(
        "/api/v1/wallet",
        headers={"Authorization": "Bearer token-user-driver-verified"},
    ).json()
    assert Decimal(str(driver_wallet["balance"])) > Decimal("0.00")

    # 4. Check NGO wallet reservation was captured (reserved_balance == 0)
    ngo_wallet = client.get(
        "/api/v1/wallet",
        headers={"Authorization": "Bearer token-user-receiver-verified"},
    ).json()
    assert Decimal(str(ngo_wallet["reserved_balance"])) == Decimal("0.00")

    # 5. Idempotent re-settlement returns ALREADY_SETTLED without duplicate transactions
    resettle = client.post(
        f"/api/v1/deliveries/{delivery_id}/settle",
        headers={"Authorization": "Bearer token-user-driver-verified"},
    )
    assert resettle.status_code == 200
    assert resettle.json()["status"] == "ALREADY_SETTLED"


def test_administrative_refund_flow(client: TestClient, mock_db: MockSupabaseClient):
    """Test administrative refund after settlement and over-refund rejection."""
    setup = setup_pricing_delivery(client, mock_db)
    delivery_id = setup["delivery_id"]

    # Top-up, reserve, advance to DELIVERED and settle
    client.post(
        "/api/v1/wallet/top-up",
        headers={"Authorization": "Bearer token-user-receiver-verified"},
        json={"amount": 1000.00},
    )
    client.post(
        f"/api/v1/deliveries/{delivery_id}/reserve",
        headers={"Authorization": "Bearer token-user-receiver-verified"},
    )
    mock_db.deliveries[delivery_id].update({
        "status": "DELIVERED",
        "driver_id": "drp-1",
    })
    client.post(
        f"/api/v1/deliveries/{delivery_id}/settle",
        headers={"Authorization": "Bearer token-user-driver-verified"},
    )

    # 1. Non-admin cannot issue refund -> 403
    unauth = client.post(
        f"/api/v1/deliveries/{delivery_id}/refund",
        headers={"Authorization": "Bearer token-user-receiver-verified"},
        json={"reason": "Self refund"},
    )
    assert unauth.status_code == 403

    # 2. Admin issues partial refund of ₹50
    rfnd_res = client.post(
        f"/api/v1/deliveries/{delivery_id}/refund",
        headers={"Authorization": "Bearer token-user-admin"},
        json={"amount": 50.00, "reason": "Minor transit delay accommodation"},
    )
    assert rfnd_res.status_code == 200
    assert rfnd_res.json()["status"] == "COMPLETED"
    assert Decimal(str(rfnd_res.json()["refund_amount"])) == Decimal("50.00")

    # 3. Excessive refund (> captured amount) rejected
    excessive_res = client.post(
        f"/api/v1/deliveries/{delivery_id}/refund",
        headers={"Authorization": "Bearer token-user-admin"},
        json={"amount": 99999.00, "reason": "Over refund"},
    )
    assert excessive_res.status_code == 422


def test_donor_subscriptions_workflow(client: TestClient, mock_db: MockSupabaseClient):
    """Test donor subscription plans, checkout, and cancellation."""
    # 1. List subscription plans
    plans_res = client.get("/api/v1/subscription-plans")
    assert plans_res.status_code == 200
    plans = plans_res.json()
    assert len(plans) >= 3
    plan_names = [p["name"] for p in plans]
    assert "Starter" in plan_names
    assert "Business" in plan_names
    assert "Enterprise" in plan_names

    # Find Business plan
    biz_plan = next(p for p in plans if p["name"] == "Business")

    # 2. Non-donor cannot purchase subscription -> 403
    unauth = client.post(
        "/api/v1/subscriptions/checkout",
        headers={"Authorization": "Bearer token-user-receiver-verified"},
        json={"plan_id": biz_plan["id"], "billing_cycle": "MONTHLY"},
    )
    assert unauth.status_code == 403

    # 3. Donor purchases Business plan
    checkout_res = client.post(
        "/api/v1/subscriptions/checkout",
        headers={"Authorization": "Bearer token-user-donor-verified"},
        json={"plan_id": biz_plan["id"], "billing_cycle": "MONTHLY"},
    )
    assert checkout_res.status_code == 201
    sub = checkout_res.json()
    assert sub["status"] == "ACTIVE"
    assert sub["plan_name"] == "Business"
    assert Decimal(str(sub["amount"])) == Decimal(str(biz_plan["monthly_price"]))

    # 4. Fetch donor current subscription
    my_sub = client.get(
        "/api/v1/subscription",
        headers={"Authorization": "Bearer token-user-donor-verified"},
    ).json()
    assert my_sub["plan_id"] == biz_plan["id"]

    # 5. Cancel subscription
    cancel_res = client.post(
        "/api/v1/subscriptions/cancel",
        headers={"Authorization": "Bearer token-user-donor-verified"},
    )
    assert cancel_res.status_code == 200
    assert cancel_res.json()["status"] == "CANCELLED"
