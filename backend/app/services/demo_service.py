"""Demo seed & reset service — Phase 19.

Uses DEMO_NAMESPACE_TAG to isolate demo records. Never deletes records
that do not carry the namespace tag. Safe by default.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional
from app.core.config import settings
from app.db.supabase import SupabaseClient

logger = logging.getLogger("annasetu.services.demo")

NAMESPACE_TAG = "demo_namespace_tag"
NAMESPACE_VALUE = "DEMO_SCENARIO_1"

DONOR_USER_ID = "demo_donor_green_leaf"
RECEIVER_A_USER_ID = "demo_receiver_seva_kitchen"
RECEIVER_B_USER_ID = "demo_receiver_anna_sadan"
DRIVER_USER_ID = "demo_driver_arjun_sharma"
ADMIN_USER_ID = "demo_admin_ops"

DONATION_ID = "demo_don_greenleaf_001"
NEED_A_ID = "demo_need_seva_001"
NEED_B_ID = "demo_need_anna_001"
MATCH_A_ID = "demo_match_seva_001"
MATCH_B_ID = "demo_match_anna_001"
ALLOC_A_ID = "demo_alloc_seva_001"
ALLOC_B_ID = "demo_alloc_anna_001"
DELIVERY_ID = "demo_del_001"
WALLET_RECEIVER_A = "demo_wallet_seva"
WALLET_DRIVER = "demo_wallet_arjun"
SEAL_ID = "demo_seal_001"
INTEGRITY_ID = "demo_integrity_001"
IMPACT_ID = "demo_impact_001"
EXCEPTION_DELIVERY_ID = "demo_del_exception_001"

MEAL_KG_EQUIVALENT = 3
CO2_KG_PER_KG_FOOD = 2.0


def _ns() -> Dict[str, Any]:
    return {NAMESPACE_TAG: NAMESPACE_VALUE}


def _tag(record: Dict[str, Any]) -> Dict[str, Any]:
    return {**record, **_ns()}


DEMO_TABLES: List[str] = [
    "impact_records",
    "food_integrity_checks",
    "handoff_evidence",
    "package_seals",
    "handoff_verifications",
    "delivery_stops",
    "delivery_offers",
    "deliveries",
    "wallet_reservations",
    "transactions",
    "wallets",
    "donation_allocations",
    "matches",
    "donations",
    "ngo_needs",
    "notifications",
    "verification_documents",
    "verification_records",
    "driver_profiles",
    "receiver_profiles",
    "donor_profiles",
    "locations",
    "profiles",
]


class DemoService:
    """Demo seeding and reset service.

    Only active when settings.demo_enabled_safely is True.
    """

    def __init__(self, db: SupabaseClient):
        self.db = db

    @property
    def enabled(self) -> bool:
        return settings.demo_enabled_safely

    # ── Reset ────────────────────────────────────────────────

    async def reset_demo_data(self) -> Dict[str, Any]:
        """Remove only demo-tagged records. Non-demo data is never touched."""
        if not self.enabled:
            raise self._disabled_error()

        removed: Dict[str, int] = {}
        # Delete from most-dependent tables first to avoid FK surprises.
        for table in DEMO_TABLES:
            try:
                existing = await self.db.query(
                    table,
                    params={f"{NAMESPACE_TAG}": f"eq.{NAMESPACE_VALUE}"},
                    select="id",
                )
                if existing:
                    for rec in existing:
                        try:
                            await self.db._raw_delete(table, rec["id"])  # type: ignore[attr-defined]
                        except Exception:
                            pass
                    removed[table] = len(existing)
            except Exception as exc:
                logger.warning("Demo reset skipped table %s: %s", table, exc)

        logger.info("Demo reset complete. Removed: %s", removed)
        return {
            "namespace": NAMESPACE_VALUE,
            "removed_records_by_table": removed,
            "completed_at": datetime.now(timezone.utc).isoformat(),
        }

    # ── Seed ─────────────────────────────────────────────────

    async def seed_demo_scenario(self) -> Dict[str, Any]:
        """Create the canonical hackathon demo dataset using the Green Leaf scenario.

        Idempotent — if records already exist they are left in place.
        """
        if not self.enabled:
            raise self._disabled_error()

        now = datetime.now(timezone.utc)
        today_2pm = now.replace(hour=14, minute=0, second=0, microsecond=0)
        if today_2pm > now:
            today_2pm = today_2pm - timedelta(days=1)
        today_6pm = today_2pm + timedelta(hours=4)
        today_8pm = today_2pm + timedelta(hours=6)
        pickup_at = today_2pm + timedelta(minutes=45)
        deliver_a_at = pickup_at + timedelta(minutes=20)
        deliver_b_at = deliver_a_at + timedelta(minutes=15)

        created: Dict[str, List[str]] = {}

        def _log(table: str, _id: str):
            created.setdefault(table, []).append(_id)

        # 1) Profiles + role profiles
        await self._upsert(
            "profiles",
            _tag(
                {
                    "id": DONOR_USER_ID,
                    "full_name": "Green Leaf Catering",
                    "phone": "+919876500001",
                    "role": "DONOR",
                    "is_active": True,
                    "email": "operations@greenleafcatering.demo",
                }
            ),
            _log,
        )
        await self._upsert(
            "profiles",
            _tag(
                {
                    "id": RECEIVER_A_USER_ID,
                    "full_name": "Seva Community Kitchen",
                    "phone": "+919876500002",
                    "role": "RECEIVER",
                    "is_active": True,
                    "email": "team@sevakitchen.demo",
                }
            ),
            _log,
        )
        await self._upsert(
            "profiles",
            _tag(
                {
                    "id": RECEIVER_B_USER_ID,
                    "full_name": "Anna Sadan Charitable Trust",
                    "phone": "+919876500003",
                    "role": "RECEIVER",
                    "is_active": True,
                    "email": "trust@annasadan.demo",
                }
            ),
            _log,
        )
        await self._upsert(
            "profiles",
            _tag(
                {
                    "id": DRIVER_USER_ID,
                    "full_name": "Arjun Sharma",
                    "phone": "+919876500004",
                    "role": "DRIVER",
                    "is_active": True,
                    "email": "arjun.delivery@annasetu.demo",
                }
            ),
            _log,
        )
        await self._upsert(
            "profiles",
            _tag(
                {
                    "id": ADMIN_USER_ID,
                    "full_name": "AnnaSetu Demo Admin",
                    "phone": "+919876500009",
                    "role": "ADMIN",
                    "is_active": True,
                    "email": "demo-admin@annasetu.demo",
                }
            ),
            _log,
        )

        # Role profiles
        await self._upsert(
            "donor_profiles",
            _tag(
                {
                    "id": "dp-green-leaf",
                    "user_id": DONOR_USER_ID,
                    "business_name": "Green Leaf Catering",
                    "business_type": "Catering Service",
                    "fssai_license_number": "11223009900099",
                    "gstin": "07DLCCS9999A1ZD",
                    "verification_status": "VERIFIED",
                    "subscription_plan": "BUSINESS",
                }
            ),
            _log,
            pk="id",
        )
        await self._upsert(
            "receiver_profiles",
            _tag(
                {
                    "id": "rp-seva",
                    "user_id": RECEIVER_A_USER_ID,
                    "organization_name": "Seva Community Kitchen",
                    "darpan_id": "NGO/DL/2020/0099999",
                    "verification_status": "VERIFIED",
                    "beneficiary_count": 220,
                }
            ),
            _log,
            pk="id",
        )
        await self._upsert(
            "receiver_profiles",
            _tag(
                {
                    "id": "rp-anna",
                    "user_id": RECEIVER_B_USER_ID,
                    "organization_name": "Anna Sadan Charitable Trust",
                    "darpan_id": "NGO/DL/2019/0088888",
                    "verification_status": "VERIFIED",
                    "beneficiary_count": 140,
                }
            ),
            _log,
            pk="id",
        )
        await self._upsert(
            "driver_profiles",
            _tag(
                {
                    "id": "drp-arjun",
                    "user_id": DRIVER_USER_ID,
                    "vehicle_type": "Insulated Van",
                    "vehicle_number": "DL 12 CA 4455",
                    "vehicle_capacity_kg": 500.0,
                    "is_online": True,
                    "availability_status": "ON_JOB",
                    "verification_status": "VERIFIED",
                    "license_number": "DL-0720180099999",
                    "current_latitude": 28.6050,
                    "current_longitude": 77.2100,
                }
            ),
            _log,
            pk="id",
        )

        # Verification records
        for uid, role in [
            (DONOR_USER_ID, "DONOR"),
            (RECEIVER_A_USER_ID, "RECEIVER"),
            (RECEIVER_B_USER_ID, "RECEIVER"),
            (DRIVER_USER_ID, "DRIVER"),
        ]:
            await self._upsert(
                "verification_records",
                _tag(
                    {
                        "id": f"verif-{uid}",
                        "user_id": uid,
                        "role": role,
                        "status": "VERIFIED",
                        "submitted_at": (now - timedelta(days=30)).isoformat(),
                        "reviewed_at": (now - timedelta(days=28)).isoformat(),
                        "reviewed_by": ADMIN_USER_ID,
                    }
                ),
                _log,
            )

        # Locations
        locs = {
            "loc-donor-greenleaf": (
                DONOR_USER_ID,
                "Plot 14, Ashok Nagar, C-Scheme, Jaipur",
                "Jaipur",
                26.9095,
                75.8016,
            ),
            "loc-rx-seva": (
                RECEIVER_A_USER_ID,
                "Sector 3 Community Hall, Malviya Nagar, Jaipur",
                "Jaipur",
                26.8524,
                75.8194,
            ),
            "loc-rx-anna": (
                RECEIVER_B_USER_ID,
                "Amrapali Marg, Vaishali Nagar, Jaipur",
                "Jaipur",
                26.9048,
                75.7423,
            ),
        }
        for lid, (uid, addr, city, lat, lng) in locs.items():
            await self._upsert(
                "locations",
                _tag(
                    {
                        "id": lid,
                        "user_id": uid,
                        "address_line1": addr,
                        "city": city,
                        "state": "Haryana",
                        "postal_code": "122001",
                        "latitude": lat,
                        "longitude": lng,
                        "is_default": True,
                    }
                ),
                _log,
                pk="id",
            )

        # 2) Needs
        await self._upsert(
            "ngo_needs",
            _tag(
                {
                    "id": NEED_A_ID,
                    "receiver_id": RECEIVER_A_USER_ID,
                    "meal_period": "LUNCH",
                    "food_type": "VEGETARIAN",
                    "categories": ["cooked-meals"],
                    "required_quantity_kg": 20,
                    "minimum_quantity_kg": 10,
                    "remaining_quantity_kg": 8,
                    "required_by": today_8pm.isoformat(),
                    "current_capacity": 30,
                    "receiving_hours_open": "18:00",
                    "receiving_hours_close": "20:00",
                    "status": "PARTIALLY_FULFILLED",
                    "location_id": "loc-rx-seva",
                    "latitude": 28.4595,
                    "longitude": 77.0665,
                    "created_at": today_2pm.isoformat(),
                }
            ),
            _log,
        )
        await self._upsert(
            "ngo_needs",
            _tag(
                {
                    "id": NEED_B_ID,
                    "receiver_id": RECEIVER_B_USER_ID,
                    "meal_period": "LUNCH",
                    "food_type": "VEGETARIAN",
                    "categories": ["cooked-meals"],
                    "required_quantity_kg": 15,
                    "minimum_quantity_kg": 6,
                    "remaining_quantity_kg": 3,
                    "required_by": today_8pm.isoformat(),
                    "current_capacity": 25,
                    "receiving_hours_open": "18:30",
                    "receiving_hours_close": "20:30",
                    "status": "PARTIALLY_FULFILLED",
                    "location_id": "loc-rx-anna",
                    "latitude": 28.4730,
                    "longitude": 77.0015,
                    "created_at": (today_2pm - timedelta(minutes=10)).isoformat(),
                }
            ),
            _log,
        )

        # 3) Donation 40 kg
        await self._upsert(
            "donations",
            _tag(
                {
                    "id": DONATION_ID,
                    "donor_id": DONOR_USER_ID,
                    "food_type": "VEGETARIAN",
                    "category": "cooked-meals",
                    "name": "Vegetarian Cooked Meals",
                    "description": "Freshly prepared North Indian thali: roti, dal, sabzi, rice. Refrigerated pickup available.",
                    "total_quantity_kg": 40,
                    "remaining_quantity_kg": 20,
                    "unit": "kg",
                    "preparation_time": today_2pm.isoformat(),
                    "available_from": (today_2pm + timedelta(minutes=30)).isoformat(),
                    "rescue_deadline": today_6pm.isoformat(),
                    "pickup_address": "14 Sector 17, Gurugram",
                    "pickup_city": "Gurugram",
                    "pickup_state": "Haryana",
                    "pickup_postal_code": "122001",
                    "pickup_latitude": 28.4660,
                    "pickup_longitude": 77.0328,
                    "storage_condition": "REFRIGERATED",
                    "storage_info": "Insulated containers · 4 °C",
                    "packaging": "Sealed food-grade stainless steel containers",
                    "allergen_info": "Contains dairy, wheat, mustard oil. Verify before serving.",
                    "image_path": None,
                    "status": "IN_TRANSIT",
                    "priority_score": 94,
                    "created_at": (today_2pm - timedelta(minutes=5)).isoformat(),
                }
            ),
            _log,
        )

        # 4) Matches
        await self._upsert(
            "matches",
            _tag(
                {
                    "id": MATCH_A_ID,
                    "donation_id": DONATION_ID,
                    "need_id": NEED_A_ID,
                    "score": 94,
                    "distance_km": 3.9,
                    "eta_minutes": 15,
                    "expiry_buffer_hours": 3.6,
                    "quantity_fulfillment_pct": 60,
                    "capacity_utilization_pct": 67,
                    "route_feasibility_score": 96,
                    "status": "CONFIRMED",
                    "created_at": (today_2pm + timedelta(minutes=5)).isoformat(),
                }
            ),
            _log,
        )
        await self._upsert(
            "matches",
            _tag(
                {
                    "id": MATCH_B_ID,
                    "donation_id": DONATION_ID,
                    "need_id": NEED_B_ID,
                    "score": 88,
                    "distance_km": 4.7,
                    "eta_minutes": 18,
                    "expiry_buffer_hours": 3.4,
                    "quantity_fulfillment_pct": 80,
                    "capacity_utilization_pct": 48,
                    "route_feasibility_score": 91,
                    "status": "CONFIRMED",
                    "created_at": (today_2pm + timedelta(minutes=7)).isoformat(),
                }
            ),
            _log,
        )

        # 5) Allocations — 12 kg + 8 kg = 20 kg allocated (remaining 20 kg)
        alloc_a_kg = 12
        alloc_b_kg = 8
        await self._upsert(
            "donation_allocations",
            _tag(
                {
                    "id": ALLOC_A_ID,
                    "donation_id": DONATION_ID,
                    "need_id": NEED_A_ID,
                    "receiver_id": RECEIVER_A_USER_ID,
                    "quantity_kg": alloc_a_kg,
                    "status": "CONFIRMED",
                    "pricing_base_inr": Decimal("480.00"),
                    "platform_fee_inr": Decimal("57.60"),
                    "driver_payout_inr": Decimal("158.40"),
                    "created_at": (today_2pm + timedelta(minutes=12)).isoformat(),
                }
            ),
            _log,
        )
        await self._upsert(
            "donation_allocations",
            _tag(
                {
                    "id": ALLOC_B_ID,
                    "donation_id": DONATION_ID,
                    "need_id": NEED_B_ID,
                    "receiver_id": RECEIVER_B_USER_ID,
                    "quantity_kg": alloc_b_kg,
                    "status": "CONFIRMED",
                    "pricing_base_inr": Decimal("320.00"),
                    "platform_fee_inr": Decimal("38.40"),
                    "driver_payout_inr": Decimal("105.60"),
                    "created_at": (today_2pm + timedelta(minutes=14)).isoformat(),
                }
            ),
            _log,
        )

        # 6) Wallets + reservation
        await self._upsert(
            "wallets",
            _tag(
                {
                    "id": WALLET_RECEIVER_A,
                    "owner_id": RECEIVER_A_USER_ID,
                    "owner_type": "RECEIVER",
                    "balance": Decimal("8420.00"),
                    "reserved_balance": Decimal("480.00"),
                    "currency": "INR",
                    "is_active": True,
                }
            ),
            _log,
            pk="id",
        )
        await self._upsert(
            "wallets",
            _tag(
                {
                    "id": WALLET_DRIVER,
                    "owner_id": DRIVER_USER_ID,
                    "owner_type": "DRIVER",
                    "balance": Decimal("12840.00"),
                    "reserved_balance": Decimal("0"),
                    "currency": "INR",
                    "is_active": True,
                }
            ),
            _log,
            pk="id",
        )
        await self._upsert(
            "wallet_reservations",
            _tag(
                {
                    "id": "demo_res_001",
                    "wallet_id": WALLET_RECEIVER_A,
                    "allocation_id": ALLOC_A_ID,
                    "delivery_id": DELIVERY_ID,
                    "amount": Decimal("480.00"),
                    "status": "RESERVED",
                    "reserved_at": (today_2pm + timedelta(minutes=16)).isoformat(),
                    "expires_at": today_8pm.isoformat(),
                }
            ),
            _log,
        )

        # 7) Delivery + stops
        total_payout = Decimal("264.00")
        await self._upsert(
            "deliveries",
            _tag(
                {
                    "id": DELIVERY_ID,
                    "donation_id": DONATION_ID,
                    "driver_id": DRIVER_USER_ID,
                    "allocation_ids": [ALLOC_A_ID, ALLOC_B_ID],
                    "status": "IN_TRANSIT",
                    "route_distance_km": 9.1,
                    "route_estimated_minutes": 35,
                    "driver_estimated_earnings": total_payout,
                    "platform_fee_inr": Decimal("96.00"),
                    "created_at": (today_2pm + timedelta(minutes=20)).isoformat(),
                    "driver_accepted_at": (today_2pm + timedelta(minutes=22)).isoformat(),
                }
            ),
            _log,
        )
        stops = [
            ("st-1", 1, "PICKUP", DONOR_USER_ID, "Green Leaf Catering", 28.4660, 77.0328, 40, "COMPLETED", pickup_at),
            ("st-2", 2, "DELIVERY", RECEIVER_A_USER_ID, "Seva Community Kitchen", 28.4595, 77.0665, alloc_a_kg, "IN_PROGRESS", None),
            ("st-3", 3, "DELIVERY", RECEIVER_B_USER_ID, "Anna Sadan Charitable Trust", 28.4730, 77.0015, alloc_b_kg, "PENDING", None),
        ]
        for sid, order, stype, eid, ename, lat, lng, qty, sstatus, completed_at in stops:
            payload: Dict[str, Any] = _tag(
                {
                    "id": sid,
                    "delivery_id": DELIVERY_ID,
                    "stop_order": order,
                    "stop_type": stype,
                    "entity_id": eid,
                    "entity_name": ename,
                    "latitude": lat,
                    "longitude": lng,
                    "quantity_kg": qty,
                    "status": sstatus,
                }
            )
            if completed_at is not None:
                payload["completed_at"] = completed_at.isoformat()
            await self._upsert("delivery_stops", payload, _log, pk="id")

        # Offers record (accepted)
        await self._upsert(
            "delivery_offers",
            _tag(
                {
                    "id": "demo_off_001",
                    "delivery_id": DELIVERY_ID,
                    "driver_id": DRIVER_USER_ID,
                    "status": "ACCEPTED",
                    "offered_at": (today_2pm + timedelta(minutes=21)).isoformat(),
                    "accepted_at": (today_2pm + timedelta(minutes=22)).isoformat(),
                    "estimated_earnings": total_payout,
                }
            ),
            _log,
        )

        # 8) Handoff verification (pickup complete) + seal
        await self._upsert(
            "handoff_verifications",
            _tag(
                {
                    "id": "hv-pickup-001",
                    "delivery_id": DELIVERY_ID,
                    "stop_id": "st-1",
                    "handoff_type": "PICKUP",
                    "gps_verified": True,
                    "otp_verified": True,
                    "otp_code": "4729",
                    "package_sealed": True,
                    "seal_id": SEAL_ID,
                    "verifier_id": DRIVER_USER_ID,
                    "verified_at": pickup_at.isoformat(),
                }
            ),
            _log,
        )
        await self._upsert(
            "package_seals",
            _tag(
                {
                    "id": SEAL_ID,
                    "delivery_id": DELIVERY_ID,
                    "seal_code": "AS-GL-000047",
                    "seal_applied_by": DRIVER_USER_ID,
                    "seal_applied_at": pickup_at.isoformat(),
                    "photo_evidence_path": None,
                    "seal_status": "INTACT",
                }
            ),
            _log,
        )
        # Handoff evidence
        await self._upsert(
            "handoff_evidence",
            _tag(
                {
                    "id": "ev-pickup-001",
                    "handoff_verification_id": "hv-pickup-001",
                    "evidence_type": "SEAL_PHOTO",
                    "storage_path": None,
                    "captured_by": DRIVER_USER_ID,
                    "captured_at": pickup_at.isoformat(),
                    "description": "Package seal AS-GL-000047 applied to insulated van.",
                }
            ),
            _log,
        )

        # 9) Integrity check (mid-delivery)
        await self._upsert(
            "food_integrity_checks",
            _tag(
                {
                    "id": INTEGRITY_ID,
                    "delivery_id": DELIVERY_ID,
                    "checkpoint_type": "IN_TRANSIT",
                    "check_performed_by": DRIVER_USER_ID,
                    "performed_at": (pickup_at + timedelta(minutes=5)).isoformat(),
                    "temperature_celsius": 5.2,
                    "seal_intact": True,
                    "package_condition": "GOOD",
                    "notes": "Insulated van doors remain sealed. No visible package damage.",
                    "ai_image_consistency_score": 92,
                    "ai_signal_enabled": settings.AI_ENABLED,
                    "result": "PASS",
                }
            ),
            _log,
        )

        # 10) Notifications (mix of history)
        for idx, (uid, title, body, urgency) in enumerate(
            [
                (DONOR_USER_ID, "40 kg donation matched", "Your donation has been matched with verified receiving organizations.", "info"),
                (RECEIVER_A_USER_ID, "12 kg allocated", "Rescue Priority 94 — accept allocation before the deadline.", "urgent"),
                (DRIVER_USER_ID, "New delivery offer", "Pickup: Green Leaf Catering · 2 stops · ₹264 payout", "info"),
                (RECEIVER_B_USER_ID, "Incoming delivery assigned", "Arjun Sharma is en route with 8 kg of rescue meals.", "success"),
                (DONOR_USER_ID, "Pickup complete", "Package seal AS-GL-000047 applied. First delivery stop underway.", "success"),
            ],
            start=1,
        ):
            await self._upsert(
                "notifications",
                _tag(
                    {
                        "id": f"demo_notif_{idx:03d}",
                        "user_id": uid,
                        "title": title,
                        "body": body,
                        "urgency": urgency,
                        "read": idx != 2,
                        "created_at": (today_2pm + timedelta(minutes=10 + idx * 4)).isoformat(),
                    }
                ),
                _log,
            )

        # 11) Impact record (from hypothetical earlier completed delivery — for dashboards)
        await self._upsert(
            "impact_records",
            _tag(
                {
                    "id": IMPACT_ID,
                    "donation_id": DONATION_ID,
                    "delivery_id": DELIVERY_ID,
                    "food_rescued_kg": 20,
                    "meal_equivalents": 20 * MEAL_KG_EQUIVALENT,
                    "estimated_co2e_avoided_kg": round(20 * CO2_KG_PER_KG_FOOD, 1),
                    "beneficiaries_reached": 60,
                    "settled_driver_payout_inr": Decimal("0.00"),
                    "settled_platform_fee_inr": Decimal("0.00"),
                    "recorded_at": None,
                    "status": "PENDING_DELIVERY_COMPLETION",
                }
            ),
            _log,
        )

        # 12) Operational exception (demo example for admin console)
        await self._upsert(
            "deliveries",
            _tag(
                {
                    "id": EXCEPTION_DELIVERY_ID,
                    "donation_id": DONATION_ID,
                    "driver_id": "user-driver-exception",
                    "allocation_ids": [],
                    "status": "REASSIGNMENT_REQUIRED",
                    "route_distance_km": 6.5,
                    "route_estimated_minutes": 28,
                    "driver_estimated_earnings": Decimal("186.00"),
                    "platform_fee_inr": Decimal("0.00"),
                    "created_at": (today_2pm - timedelta(hours=2)).isoformat(),
                    "exception_reason": "Driver unavailable — reported vehicle mechanical issue.",
                    "exception_reported_at": (today_2pm - timedelta(hours=1)).isoformat(),
                }
            ),
            _log,
        )
        await self._upsert(
            "food_integrity_checks",
            _tag(
                {
                    "id": "demo_integrity_review_001",
                    "delivery_id": DELIVERY_ID,
                    "checkpoint_type": "PICKUP_CONSISTENCY",
                    "check_performed_by": ADMIN_USER_ID,
                    "performed_at": (pickup_at + timedelta(minutes=2)).isoformat(),
                    "seal_intact": True,
                    "package_condition": "NEEDS_REVIEW",
                    "notes": "Donor-declared 40 kg and seal photo look consistent. Minor labelling variance flagged for review.",
                    "ai_image_consistency_score": 81,
                    "ai_signal_enabled": settings.AI_ENABLED,
                    "result": "REVIEW_REQUIRED",
                    "admin_review_note": "Integrity review example — flagged to show operational handling.",
                }
            ),
            _log,
        )

        summary = {
            "scenario": "Green Leaf Catering — 40 kg Vegetarian Cooked Meals",
            "namespace": NAMESPACE_VALUE,
            "demo_mode_enabled": True,
            "entities": {
                "donor": "Green Leaf Catering",
                "receivers": ["Seva Community Kitchen (20 kg need · 12 kg allocated)", "Anna Sadan Charitable Trust (15 kg need · 8 kg allocated)"],
                "driver": "Arjun Sharma · DL 12 CA 4455 · Insulated Van",
                "donation": "40 kg · 20 kg allocated · 20 kg remaining",
                "delivery": f"{DELIVERY_ID} · IN_TRANSIT · 3 stops · ₹{total_payout} driver payout",
            },
            "created_records_count": {k: len(v) for k, v in created.items()},
            "operational_examples": {
                "integrity_review": "demo_integrity_review_001 — PENDING admin review",
                "delivery_exception": f"{EXCEPTION_DELIVERY_ID} — REASSIGNMENT_REQUIRED",
                "wallet_reservation": f"₹480.00 reserved against {WALLET_RECEIVER_A}",
            },
            "seeded_at": datetime.now(timezone.utc).isoformat(),
        }
        logger.info("Demo seed complete — scenario: %s", summary["scenario"])
        return summary

    # ── Helpers ───────────────────────────────────────────────

    async def _upsert(
        self,
        table: str,
        payload: Dict[str, Any],
        logger_cb,
        pk: str = "id",
    ) -> None:
        try:
            await self.db.upsert(table, payload, on_conflict=pk)
            logger_cb(table, payload.get(pk, "?"))
        except Exception as exc:
            logger.info("Demo seed — fallback insert for %s %s: %s", table, payload.get(pk), exc)
            try:
                await self.db.insert(table, payload)
                logger_cb(table, payload.get(pk, "?"))
            except Exception as exc2:
                logger.warning("Demo seed could not upsert %s %s: %s", table, payload.get(pk), exc2)

    def _disabled_error(self) -> Exception:
        from app.utils.exceptions import ForbiddenException

        return ForbiddenException(
            message=(
                "Demo mode is not enabled. Set DEMO_MODE=true in a non-production APP_ENV to use demo seed and reset endpoints."
            ),
            error_code="DEMO_MODE_DISABLED",
            details={
                "APP_ENV": settings.APP_ENV,
                "DEMO_MODE": settings.DEMO_MODE,
                "documentation": "See backend/.env.example — DEMO_MODE section.",
            },
        )
