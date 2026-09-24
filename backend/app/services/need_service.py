"""NGO Need Domain Service."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid
from app.db.supabase import SupabaseClient
from app.schemas.need import NeedCreate, NeedResponse, NeedStatus, NeedUpdate
from app.services.audit_service import AuditService
from app.utils.exceptions import AppException, ForbiddenException, NotFoundException, ValidationException


class NeedService:
    """Service managing NGO hunger relief food needs."""

    def __init__(self, db: SupabaseClient):
        self.db = db
        self.audit = AuditService(db)

    async def _verify_location_ownership(self, location_id: str, receiver_id: str):
        location = await self.db.get_by_id("locations", location_id, id_column="id")
        if not location:
            raise NotFoundException("Receiving center location not found.", error_code="LOCATION_NOT_FOUND")
        if location.get("user_id") != receiver_id:
            raise ForbiddenException("Location does not belong to your organization.", error_code="LOCATION_FORBIDDEN")

    async def _verify_food_category(self, food_category_id: str):
        category = await self.db.get_by_id("food_categories", food_category_id, id_column="id")
        if not category:
            raise NotFoundException("Specified food category does not exist.", error_code="CATEGORY_NOT_FOUND")
        if not category.get("is_active", True):
            raise ValidationException("Specified food category is currently inactive.", error_code="CATEGORY_INACTIVE")

    async def create_need(self, receiver_id: str, payload: NeedCreate) -> NeedResponse:
        """Create a new food need in DRAFT state."""
        # 1. Validate location belongs to receiver
        await self._verify_location_ownership(payload.location_id, receiver_id)

        # 2. Validate food category exists
        await self._verify_food_category(payload.food_category_id)

        need_id = str(uuid.uuid4())
        need_record = {
            "id": need_id,
            "receiver_id": receiver_id,
            "meal_period": payload.meal_period.value,
            "diet_type": payload.diet_type.value,
            "food_category_id": payload.food_category_id,
            "required_quantity_kg": payload.required_quantity_kg,
            "minimum_quantity_kg": payload.minimum_quantity_kg,
            "remaining_quantity_kg": payload.required_quantity_kg,
            "receiving_capacity_kg": payload.receiving_capacity_kg,
            "required_by": payload.required_by,
            "receiving_start_time": payload.receiving_start_time,
            "receiving_end_time": payload.receiving_end_time,
            "special_requirements": payload.special_requirements,
            "location_id": payload.location_id,
            "status": NeedStatus.DRAFT.value,
        }

        created = await self.db.insert("ngo_needs", need_record)
        await self.audit.log_event("NEED_CREATED", "ngo_needs", need_id, user_id=receiver_id, new_values=need_record)
        return NeedResponse(**created)

    async def list_needs(self, receiver_id: str, status: Optional[NeedStatus] = None) -> List[NeedResponse]:
        """List food needs created by the receiver."""
        params = {"receiver_id": f"eq.{receiver_id}"}
        if status:
            params["status"] = f"eq.{status.value}"

        records = await self.db.query("ngo_needs", params=params, order="created_at.desc")
        return [NeedResponse(**r) for r in records]

    async def get_need(self, need_id: str, receiver_id: Optional[str] = None) -> NeedResponse:
        """Get need details and optionally enforce receiver ownership."""
        record = await self.db.get_by_id("ngo_needs", need_id, id_column="id")
        if not record:
            raise NotFoundException("NGO Need record not found.", error_code="NEED_NOT_FOUND")

        if receiver_id and record.get("receiver_id") != receiver_id:
            raise ForbiddenException("Access forbidden. You do not own this need.", error_code="NEED_FORBIDDEN")

        return NeedResponse(**record)

    async def update_need(self, need_id: str, receiver_id: str, payload: NeedUpdate) -> NeedResponse:
        """Update need while in editable state."""
        existing = await self.get_need(need_id, receiver_id=receiver_id)

        if existing.status not in (NeedStatus.DRAFT, NeedStatus.ACTIVE):
            raise ValidationException(
                f"Cannot modify need in '{existing.status.value}' status.",
                error_code="NEED_IMMUTABLE",
            )

        fields: Dict[str, Any] = {}
        if payload.meal_period is not None:
            fields["meal_period"] = payload.meal_period.value
        if payload.diet_type is not None:
            fields["diet_type"] = payload.diet_type.value
        if payload.food_category_id is not None:
            await self._verify_food_category(payload.food_category_id)
            fields["food_category_id"] = payload.food_category_id
        if payload.location_id is not None:
            await self._verify_location_ownership(payload.location_id, receiver_id)
            fields["location_id"] = payload.location_id
        if payload.required_quantity_kg is not None:
            fields["required_quantity_kg"] = payload.required_quantity_kg
            if existing.status == NeedStatus.DRAFT:
                fields["remaining_quantity_kg"] = payload.required_quantity_kg
        if payload.minimum_quantity_kg is not None:
            fields["minimum_quantity_kg"] = payload.minimum_quantity_kg
        if payload.receiving_capacity_kg is not None:
            fields["receiving_capacity_kg"] = payload.receiving_capacity_kg
        if payload.required_by is not None:
            fields["required_by"] = payload.required_by
        if payload.receiving_start_time is not None:
            fields["receiving_start_time"] = payload.receiving_start_time
        if payload.receiving_end_time is not None:
            fields["receiving_end_time"] = payload.receiving_end_time
        if payload.special_requirements is not None:
            fields["special_requirements"] = payload.special_requirements

        if not fields:
            return existing

        updated = await self.db.update_by_id("ngo_needs", need_id, fields, id_column="id")
        return NeedResponse(**updated)

    async def activate_need(self, need_id: str, receiver_id: str) -> NeedResponse:
        """Activate a draft need after verifying target delivery time is in the future."""
        existing = await self.get_need(need_id, receiver_id=receiver_id)

        if existing.status == NeedStatus.ACTIVE:
            return existing

        if existing.status != NeedStatus.DRAFT:
            raise ValidationException(
                f"Cannot activate need in status '{existing.status.value}'.",
                error_code="INVALID_STATUS_TRANSITION",
            )

        # Check required_by is in the future
        try:
            req_time = datetime.fromisoformat(existing.required_by.replace("Z", "+00:00"))
            now = datetime.now(timezone.utc)
            if req_time <= now:
                raise ValidationException(
                    "Target required_by time must be in the future to activate need.",
                    error_code="DEADLINE_IN_PAST",
                )
        except (ValueError, TypeError):
            pass

        updated = await self.db.update_by_id("ngo_needs", need_id, {"status": NeedStatus.ACTIVE.value}, id_column="id")
        await self.audit.log_event("NEED_ACTIVATED", "ngo_needs", need_id, user_id=receiver_id, old_values={"status": existing.status.value}, new_values={"status": NeedStatus.ACTIVE.value})
        return NeedResponse(**updated)

    async def cancel_need(self, need_id: str, receiver_id: str) -> NeedResponse:
        """Cancel an open or active need."""
        existing = await self.get_need(need_id, receiver_id=receiver_id)

        if existing.status in (NeedStatus.CANCELLED, NeedStatus.FULFILLED):
            return existing

        updated = await self.db.update_by_id("ngo_needs", need_id, {"status": NeedStatus.CANCELLED.value}, id_column="id")
        await self.audit.log_event("NEED_CANCELLED", "ngo_needs", need_id, user_id=receiver_id, old_values={"status": existing.status.value}, new_values={"status": NeedStatus.CANCELLED.value})
        return NeedResponse(**updated)
