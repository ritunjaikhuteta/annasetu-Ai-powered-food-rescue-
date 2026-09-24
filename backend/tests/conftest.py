"""Test Configuration and Mock Fixtures for AnnaSetu Backend Tests."""

from typing import Any, Dict, List, Optional
import pytest
from fastapi.testclient import TestClient
from app.api.deps import get_supabase_client
from app.db.supabase import SupabaseClient
from app.main import app
from app.schemas.auth import AuthenticatedUser
from app.schemas.common import UserRole, VerificationStatus


class MockSupabaseClient(SupabaseClient):
    """Mocked in-memory Supabase client for deterministic unit testing without network or credentials."""

    def __init__(self):
        super().__init__(base_url="https://mock.supabase.co", secret_key="mock-secret")
        self.profiles: Dict[str, Dict[str, Any]] = {
            "user-donor-verified": {
                "id": "user-donor-verified",
                "full_name": "Verified Donor Chef",
                "phone": "+919876543210",
                "role": "DONOR",
                "is_active": True,
            },
            "user-donor-pending": {
                "id": "user-donor-pending",
                "full_name": "Pending Donor Restaurant",
                "phone": "+919876543211",
                "role": "DONOR",
                "is_active": True,
            },
            "user-receiver-verified": {
                "id": "user-receiver-verified",
                "full_name": "Verified NGO Director",
                "phone": "+919876543212",
                "role": "RECEIVER",
                "is_active": True,
            },
            "user-driver-verified": {
                "id": "user-driver-verified",
                "full_name": "Verified Logistics Driver",
                "phone": "+919876543213",
                "role": "DRIVER",
                "is_active": True,
            },
            "user-admin": {
                "id": "user-admin",
                "full_name": "System Administrator",
                "phone": "+919876543299",
                "role": "ADMIN",
                "is_active": True,
            },
        }

        self.donor_profiles: Dict[str, Dict[str, Any]] = {
            "user-donor-verified": {
                "id": "dp-1",
                "user_id": "user-donor-verified",
                "business_name": "Taj Catering",
                "business_type": "Hotel / Restaurant",
                "fssai_license_number": "FSSAI-12345",
                "gstin": "27AAAAA0000A1Z5",
                "verification_status": "VERIFIED",
                "subscription_plan": "FREE",
            },
            "user-donor-pending": {
                "id": "dp-2",
                "user_id": "user-donor-pending",
                "business_name": "Fresh Kitchen",
                "verification_status": "PENDING",
                "subscription_plan": "FREE",
            },
        }

        self.receiver_profiles: Dict[str, Dict[str, Any]] = {
            "user-receiver-verified": {
                "id": "rp-1",
                "user_id": "user-receiver-verified",
                "organization_name": "Feed Hope Foundation",
                "darpan_id": "DARPAN-12345",
                "verification_status": "VERIFIED",
            }
        }

        self.driver_profiles: Dict[str, Dict[str, Any]] = {
            "user-driver-verified": {
                "id": "drp-1",
                "user_id": "user-driver-verified",
                "vehicle_type": "Insulated Van",
                "vehicle_number": "MH-02-AB-1234",
                "vehicle_capacity_kg": 500.0,
                "is_online": True,
                "availability_status": "AVAILABLE",
                "verification_status": "VERIFIED",
                "current_latitude": 28.6145,
                "current_longitude": 77.2095,
            }
        }

        self.vehicle_catalog: Dict[str, Dict[str, Any]] = {
            "vc-van": {
                "id": "vc-van",
                "vehicle_type": "van",
                "capacity_kg": 500.0,
                "is_active": True,
            },
            "vc-auto": {
                "id": "vc-auto",
                "vehicle_type": "auto",
                "capacity_kg": 75.0,
                "is_active": True,
            },
            "vc-motorcycle": {
                "id": "vc-motorcycle",
                "vehicle_type": "motorcycle",
                "capacity_kg": 15.0,
                "is_active": True,
            },
        }

        self.locations: Dict[str, Dict[str, Any]] = {
            "loc-donor-1": {
                "id": "loc-donor-1",
                "user_id": "user-donor-verified",
                "address_line1": "123 Connaught Place",
                "city": "New Delhi",
                "latitude": 28.6139,
                "longitude": 77.2090,
                "is_default": True,
            },
            "loc-receiver-1": {
                "id": "loc-receiver-1",
                "user_id": "user-receiver-verified",
                "address_line1": "456 Safdarjung Enclave",
                "city": "New Delhi",
                "latitude": 28.5672,
                "longitude": 77.1982,
                "is_default": True,
            },
            "loc-other": {
                "id": "loc-other",
                "user_id": "other-user",
                "address_line1": "999 Far Away Rd",
                "city": "Gurgaon",
                "latitude": 28.4595,
                "longitude": 77.0266,
            },
        }

        self.food_categories: Dict[str, Dict[str, Any]] = {
            "cat-cooked-meals": {
                "id": "cat-cooked-meals",
                "name": "Cooked Meals",
                "code": "cooked-meals",
                "diet_type": "VEGETARIAN",
                "shelf_life_hours": 6,
                "is_active": True,
            },
            "cat-nonveg-chicken": {
                "id": "cat-nonveg-chicken",
                "name": "Chicken Curry",
                "code": "chicken",
                "diet_type": "NON_VEGETARIAN",
                "shelf_life_hours": 4,
                "is_active": True,
            },
            "cat-inactive": {
                "id": "cat-inactive",
                "name": "Inactive Food Category",
                "code": "inactive",
                "diet_type": "MIXED",
                "shelf_life_hours": 12,
                "is_active": False,
            },
        }

        self.ngo_needs: Dict[str, Dict[str, Any]] = {}
        self.donations: Dict[str, Dict[str, Any]] = {}
        self.matches: Dict[str, Dict[str, Any]] = {}
        self.donation_allocations: Dict[str, Dict[str, Any]] = {}
        self.notifications: Dict[str, Dict[str, Any]] = {}
        self.audit_logs: Dict[str, Dict[str, Any]] = {}
        self.deliveries: Dict[str, Dict[str, Any]] = {}
        self.delivery_stops: Dict[str, Dict[str, Any]] = {}
        self.delivery_offers: Dict[str, Dict[str, Any]] = {}
        self.driver_locations: Dict[str, Dict[str, Any]] = {}
        self.handoff_verifications: Dict[str, Dict[str, Any]] = {}
        self.package_seals: Dict[str, Dict[str, Any]] = {}
        self.handoff_evidence: Dict[str, Dict[str, Any]] = {}
        self.food_integrity_checks: Dict[str, Dict[str, Any]] = {}
        self.pricing_rules: Dict[str, Dict[str, Any]] = {}
        self.vehicle_pricing: Dict[str, Dict[str, Any]] = {}
        self.wallets: Dict[str, Dict[str, Any]] = {}
        self.transactions: Dict[str, Dict[str, Any]] = {}
        self.wallet_reservations: Dict[str, Dict[str, Any]] = {}
        self.subscription_plans: Dict[str, Dict[str, Any]] = {}
        self.subscriptions: Dict[str, Dict[str, Any]] = {}
        self.verification_records: Dict[str, Dict[str, Any]] = {}
        self.verification_documents: Dict[str, Dict[str, Any]] = {}
        self.impact_records: Dict[str, Dict[str, Any]] = {}
        self.impact_factors: Dict[str, Dict[str, Any]] = {}

    async def verify_user_jwt(self, token: str) -> Optional[Dict[str, Any]]:
        if token.startswith("token-"):
            user_id = token.replace("token-", "")
            if user_id in self.profiles:
                return {
                    "id": user_id,
                    "email": f"{user_id}@example.com",
                    "user_metadata": {"full_name": self.profiles[user_id].get("full_name")},
                }
        return None

    async def get_by_id(self, table: str, id_value: str, id_column: str = "id") -> Optional[Dict[str, Any]]:
        target_dict = getattr(self, table, None)
        if target_dict is None:
            return None

        for k, item in target_dict.items():
            if str(item.get(id_column)) == str(id_value) or str(k) == str(id_value):
                return dict(item)
        return None

    async def update_by_id(
        self,
        table: str,
        id_value: str,
        payload: Dict[str, Any],
        id_column: str = "id",
    ) -> Dict[str, Any]:
        target_dict = getattr(self, table, None)
        if target_dict is None:
            target_dict = {}
            setattr(self, table, target_dict)

        for k, item in target_dict.items():
            if str(item.get(id_column)) == str(id_value) or str(k) == str(id_value):
                item.update(payload)
                return dict(item)

        # Not found, insert new
        payload[id_column] = id_value
        if "id" not in payload:
            payload["id"] = id_value
        target_dict[id_value] = payload
        return dict(payload)

    async def insert(self, table: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        target_dict = getattr(self, table, None)
        if target_dict is None:
            target_dict = {}
            setattr(self, table, target_dict)

        item_id = payload.get("id", str(len(target_dict) + 1))
        payload["id"] = item_id
        target_dict[item_id] = dict(payload)
        return dict(payload)

    async def query(
        self,
        table: str,
        params: Optional[Dict[str, str]] = None,
        select: str = "*",
        order: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        target_dict = getattr(self, table, None)
        if target_dict is None:
            return []

        results = [dict(v) for v in target_dict.values()]

        if params:
            for k, condition in params.items():
                if condition.startswith("eq."):
                    val = condition[3:]
                    results = [r for r in results if str(r.get(k)) == str(val)]
                elif condition.startswith("in.(") and condition.endswith(")"):
                    options = [o.strip() for o in condition[4:-1].split(",")]
                    results = [r for r in results if str(r.get(k)) in options]

        if limit:
            results = results[:limit]

        return results

    async def upsert(
        self,
        table: str,
        payload: Dict[str, Any],
        on_conflict: str = "id",
    ) -> Dict[str, Any]:
        target_dict = getattr(self, table, None)
        if target_dict is None:
            target_dict = {}
            setattr(self, table, target_dict)

        conflict_keys = [k.strip() for k in on_conflict.split(",")]
        # Check if record matching conflict keys exists
        matched_id = None
        for item_id, item in target_dict.items():
            if all(str(item.get(k)) == str(payload.get(k)) for k in conflict_keys):
                matched_id = item_id
                break

        if matched_id:
            target_dict[matched_id].update(payload)
            return dict(target_dict[matched_id])
        else:
            return await self.insert(table, payload)

    async def compare_and_swap_update(
        self,
        table: str,
        id_value: str,
        expected_field: str,
        expected_val: Any,
        new_values: Dict[str, Any],
        id_column: str = "id",
    ) -> Optional[Dict[str, Any]]:
        target_dict = getattr(self, table, None)
        if target_dict is None:
            return None

        existing = await self.get_by_id(table, id_value, id_column=id_column)
        if not existing:
            return None

        # Compare float values with tolerance or exact
        actual_val = existing.get(expected_field)
        match = False
        if isinstance(actual_val, (int, float)) and isinstance(expected_val, (int, float)):
            match = abs(float(actual_val) - float(expected_val)) < 0.001
        else:
            match = str(actual_val) == str(expected_val)

        if not match:
            return None

        existing.update(new_values)
        target_dict[existing["id"]] = existing
        return dict(existing)


@pytest.fixture
def mock_db() -> MockSupabaseClient:
    return MockSupabaseClient()


@pytest.fixture
def client(mock_db: MockSupabaseClient) -> TestClient:
    app.dependency_overrides[get_supabase_client] = lambda: mock_db
    test_client = TestClient(app)
    yield test_client
    app.dependency_overrides.clear()
