"""Admin Operations Command Center Service."""

from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional
from app.db.supabase import SupabaseClient
from app.schemas.admin import PaginatedResponse
from app.schemas.admin_operations import (
    ActiveRescueDelivery,
    AdminUserItem,
    DeliveryExceptionItem,
    ReassignDeliveryRequest,
)
from app.services.audit_service import AuditService
from app.services.notification_service import NotificationService
from app.utils.exceptions import NotFoundException, ValidationException

logger = logging.getLogger("annasetu.services.admin_operations")


class AdminOperationsService:
    """Handles operational monitoring, user controls, exceptions, and rescue reassignments."""

    def __init__(self, db: SupabaseClient):
        self.db = db
        self.audit = AuditService(db)
        self.notification = NotificationService(db)

    # =========================================================================
    # 1. USER DIRECTORY & ACTIONS
    # =========================================================================

    async def list_users(
        self,
        role: Optional[str] = None,
        verification_status: Optional[str] = None,
        is_active: Optional[bool] = None,
        search: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> PaginatedResponse[AdminUserItem]:
        """Lists users with filtering and search across names/businesses."""
        all_profiles = await self.db.query("profiles", order="created_at.desc")

        items: List[AdminUserItem] = []
        for p in all_profiles:
            uid = p.get("id", "")
            p_role = p.get("role", "")
            p_active = p.get("is_active", True)

            if role and p_role.upper() != role.upper():
                continue
            if is_active is not None and p_active != is_active:
                continue

            # Fetch role-specific details & verification status
            v_status = None
            org_or_biz = None
            if p_role == "DONOR":
                dp = await self.db.get_by_id("donor_profiles", uid, id_column="user_id") or {}
                v_status = dp.get("verification_status", "PENDING")
                org_or_biz = dp.get("business_name")
            elif p_role == "RECEIVER":
                rp = await self.db.get_by_id("receiver_profiles", uid, id_column="user_id") or {}
                v_status = rp.get("verification_status", "PENDING")
                org_or_biz = rp.get("organization_name")
            elif p_role == "DRIVER":
                drp = await self.db.get_by_id("driver_profiles", uid, id_column="user_id") or {}
                v_status = drp.get("verification_status", "PENDING")
                org_or_biz = drp.get("vehicle_number")

            if verification_status and v_status != verification_status:
                continue

            # Search filter
            if search:
                term = search.lower()
                name = str(p.get("full_name", "")).lower()
                phone = str(p.get("phone", "")).lower()
                biz = str(org_or_biz or "").lower()
                if term not in name and term not in phone and term not in biz:
                    continue

            items.append(
                AdminUserItem(
                    id=uid,
                    full_name=p.get("full_name"),
                    email=p.get("email"),
                    phone=p.get("phone"),
                    role=p_role,
                    is_active=p_active,
                    verification_status=v_status,
                    created_at=p.get("created_at"),
                    business_or_org_name=org_or_biz,
                )
            )

        total = len(items)
        start = (page - 1) * page_size
        paginated_items = items[start : start + page_size]
        total_pages = (total + page_size - 1) // page_size if page_size > 0 else 1

        return PaginatedResponse(
            items=paginated_items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    async def get_user_detail(self, user_id: str) -> Dict[str, Any]:
        """Retrieves comprehensive user profile and role operational details."""
        profile = await self.db.get_by_id("profiles", user_id)
        if not profile:
            raise NotFoundException(f"User {user_id} not found.")

        role = profile.get("role", "")
        role_data = {}
        if role == "DONOR":
            role_data = await self.db.get_by_id("donor_profiles", user_id, id_column="user_id") or {}
        elif role == "RECEIVER":
            role_data = await self.db.get_by_id("receiver_profiles", user_id, id_column="user_id") or {}
        elif role == "DRIVER":
            role_data = await self.db.get_by_id("driver_profiles", user_id, id_column="user_id") or {}

        verifications = await self.db.query("verification_records", params={"user_id": f"eq.{user_id}"})
        documents = await self.db.query("verification_documents", params={"user_id": f"eq.{user_id}"})

        return {
            "profile": profile,
            "role_data": role_data,
            "verification_records": verifications,
            "documents": documents,
        }

    async def activate_user(self, user_id: str, admin_id: str, reason: str) -> Dict[str, Any]:
        """Activates a user profile. NEVER modifies profile.role."""
        profile = await self.db.get_by_id("profiles", user_id)
        if not profile:
            raise NotFoundException(f"User {user_id} not found.")

        now_iso = datetime.now(timezone.utc).isoformat()
        updated = await self.db.update_by_id("profiles", user_id, {"is_active": True, "updated_at": now_iso})

        await self.audit.log_event(
            action="USER_ACTIVATED",
            entity_type="profiles",
            entity_id=user_id,
            user_id=admin_id,
            new_values={"is_active": True, "reason": reason},
        )
        return updated

    async def deactivate_user(self, user_id: str, admin_id: str, reason: str) -> Dict[str, Any]:
        """Deactivates a user profile. NEVER modifies profile.role."""
        profile = await self.db.get_by_id("profiles", user_id)
        if not profile:
            raise NotFoundException(f"User {user_id} not found.")

        now_iso = datetime.now(timezone.utc).isoformat()
        updated = await self.db.update_by_id("profiles", user_id, {"is_active": False, "updated_at": now_iso})

        await self.audit.log_event(
            action="USER_DEACTIVATED",
            entity_type="profiles",
            entity_id=user_id,
            user_id=admin_id,
            new_values={"is_active": False, "reason": reason},
        )
        return updated

    # =========================================================================
    # 2. LIVE RESCUE OPERATIONS & DELIVERY EXCEPTIONS
    # =========================================================================

    async def list_active_operations(self) -> List[ActiveRescueDelivery]:
        """Lists active deliveries with driver, stops, urgency level, and handoff progress."""
        active_states = ("OPEN", "ACCEPTED", "ASSIGNED", "ARRIVING_PICKUP", "PICKED_UP", "IN_TRANSIT", "AT_STOP")
        deliveries = await self.db.query("deliveries")
        active_list = [d for d in deliveries if d.get("status") in active_states]

        results: List[ActiveRescueDelivery] = []
        for d in active_list:
            del_id = d.get("id", "")
            driver_id = d.get("driver_id")
            driver_name = None
            vehicle_type = None

            if driver_id:
                dr_prof = await self.db.get_by_id("driver_profiles", driver_id, id_column="user_id") or {}
                vehicle_type = dr_prof.get("vehicle_type")
                user_p = await self.db.get_by_id("profiles", driver_id) or {}
                driver_name = user_p.get("full_name")

            donation_id = d.get("donation_id", "")
            donation = await self.db.get_by_id("donations", donation_id) or {}
            food_name = donation.get("food_name") or donation.get("description", "Surplus Food")
            qty_kg = float(donation.get("quantity_kg", 0.0))

            stops = await self.db.query("delivery_stops", params={"delivery_id": f"eq.{del_id}"})
            completed_stops = [s for s in stops if s.get("status") in ("COMPLETED", "DELIVERED")]
            current_stop_str = f"Stop {len(completed_stops) + 1} of {len(stops)}" if stops else "Pickup"

            # Determine urgency deterministically
            status = d.get("status", "ACTIVE")
            urgency = "NORMAL"
            deadline = donation.get("pickup_deadline") or donation.get("rescue_deadline")
            if status in ("ARRIVING_PICKUP", "ACCEPTED"):
                urgency = "ELEVATED"

            results.append(
                ActiveRescueDelivery(
                    delivery_id=del_id,
                    status=status,
                    driver_id=driver_id,
                    driver_name=driver_name,
                    vehicle_type=vehicle_type,
                    donation_id=donation_id,
                    food_name=food_name,
                    quantity_kg=qty_kg,
                    pickup_location_ref=d.get("pickup_location_id") or "Donor Location",
                    delivery_stops_count=len(stops),
                    current_stop=current_stop_str,
                    estimated_eta=d.get("estimated_eta") or "20 mins",
                    deadline=deadline,
                    route_status="FEASIBLE",
                    handoff_status=d.get("handoff_status", "PENDING_PICKUP"),
                    integrity_status=d.get("integrity_status", "CLEAR"),
                    urgency_level=urgency,
                )
            )

        return results

    async def list_delivery_exceptions(self) -> List[DeliveryExceptionItem]:
        """Lists deliveries requiring administrative intervention."""
        deliveries = await self.db.query("deliveries")
        exceptions: List[DeliveryExceptionItem] = []

        for d in deliveries:
            del_id = d.get("id", "")
            status = d.get("status", "")
            driver_id = d.get("driver_id")
            created_at = d.get("created_at", "")

            if status == "REASSIGNMENT_REQUIRED":
                exceptions.append(
                    DeliveryExceptionItem(
                        delivery_id=del_id,
                        status=status,
                        exception_type="REASSIGNMENT_REQUIRED",
                        urgency="HIGH",
                        reason="Previous driver cancelled or timed out. Immediate reassignment required.",
                        driver_id=driver_id,
                        created_at=created_at,
                    )
                )
            elif status in ("FAILED_PICKUP", "FAILED_DELIVERY"):
                exceptions.append(
                    DeliveryExceptionItem(
                        delivery_id=del_id,
                        status=status,
                        exception_type="DELIVERY_FAILURE",
                        urgency="CRITICAL",
                        reason=f"Delivery entered {status}. Action required for food rescue salvage.",
                        driver_id=driver_id,
                        created_at=created_at,
                    )
                )
            elif status == "CANCELLED":
                exceptions.append(
                    DeliveryExceptionItem(
                        delivery_id=del_id,
                        status=status,
                        exception_type="CANCELLED_DELIVERY",
                        urgency="MEDIUM",
                        reason="Delivery mission was cancelled before completion.",
                        driver_id=driver_id,
                        created_at=created_at,
                    )
                )

        return exceptions

    async def reassign_delivery(
        self,
        delivery_id: str,
        admin_id: str,
        payload: ReassignDeliveryRequest,
    ) -> Dict[str, Any]:
        """Reassigns a delivery to a new verified driver using deterministic eligibility checks."""
        delivery = await self.db.get_by_id("deliveries", delivery_id)
        if not delivery:
            raise NotFoundException(f"Delivery {delivery_id} not found.")

        old_driver_id = delivery.get("driver_id")
        new_driver_id = payload.new_driver_id

        # Validate new driver exists and is verified
        new_driver_prof = await self.db.get_by_id("driver_profiles", new_driver_id, id_column="user_id")
        if not new_driver_prof:
            raise ValidationException(f"Target driver {new_driver_id} not found.")

        if new_driver_prof.get("verification_status") != "VERIFIED":
            raise ValidationException("Cannot assign delivery to unverified delivery partner.")

        if not new_driver_prof.get("is_online", True) or new_driver_prof.get("availability_status") == "BUSY":
            raise ValidationException("Target driver is currently offline or busy.")

        now_iso = datetime.now(timezone.utc).isoformat()
        update_data = {
            "driver_id": new_driver_id,
            "status": "ACCEPTED",
            "updated_at": now_iso,
        }
        updated = await self.db.update_by_id("deliveries", delivery_id, update_data)

        # Audit event preserving old driver
        await self.audit.log_event(
            action="DELIVERY_REASSIGNED",
            entity_type="deliveries",
            entity_id=delivery_id,
            user_id=admin_id,
            new_values={
                "previous_driver_id": old_driver_id,
                "new_driver_id": new_driver_id,
                "reason": payload.reason,
            },
        )

        return updated

    # =========================================================================
    # 3. DONATIONS, NEEDS, MATCHES, ALLOCATIONS INSPECTION
    # =========================================================================

    async def list_donations(
        self,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> PaginatedResponse[Dict[str, Any]]:
        params = {"status": f"eq.{status}"} if status else None
        donations = await self.db.query("donations", params=params, order="created_at.desc")
        total = len(donations)
        start = (page - 1) * page_size
        return PaginatedResponse(
            items=donations[start : start + page_size],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=(total + page_size - 1) // page_size if page_size > 0 else 1,
        )

    async def list_needs(
        self,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> PaginatedResponse[Dict[str, Any]]:
        params = {"status": f"eq.{status}"} if status else None
        needs = await self.db.query("ngo_needs", params=params, order="created_at.desc")
        total = len(needs)
        start = (page - 1) * page_size
        return PaginatedResponse(
            items=needs[start : start + page_size],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=(total + page_size - 1) // page_size if page_size > 0 else 1,
        )

    async def list_matches(
        self,
        donation_id: Optional[str] = None,
        need_id: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> PaginatedResponse[Dict[str, Any]]:
        params = {}
        if donation_id:
            params["donation_id"] = f"eq.{donation_id}"
        if need_id:
            params["need_id"] = f"eq.{need_id}"
        matches = await self.db.query("matches", params=params, order="priority_score.desc")
        total = len(matches)
        start = (page - 1) * page_size
        return PaginatedResponse(
            items=matches[start : start + page_size],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=(total + page_size - 1) // page_size if page_size > 0 else 1,
        )

    async def list_allocations(
        self,
        donation_id: Optional[str] = None,
        receiver_id: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> PaginatedResponse[Dict[str, Any]]:
        params = {}
        if donation_id:
            params["donation_id"] = f"eq.{donation_id}"
        if receiver_id:
            params["receiver_id"] = f"eq.{receiver_id}"
        allocations = await self.db.query("donation_allocations", params=params, order="created_at.desc")
        total = len(allocations)
        start = (page - 1) * page_size
        return PaginatedResponse(
            items=allocations[start : start + page_size],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=(total + page_size - 1) // page_size if page_size > 0 else 1,
        )

    async def list_drivers(
        self,
        verification_status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> PaginatedResponse[Dict[str, Any]]:
        params = {}
        if verification_status:
            params["verification_status"] = f"eq.{verification_status}"
        drivers = await self.db.query("driver_profiles", params=params)
        total = len(drivers)
        start = (page - 1) * page_size
        return PaginatedResponse(
            items=drivers[start : start + page_size],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=(total + page_size - 1) // page_size if page_size > 0 else 1,
        )
