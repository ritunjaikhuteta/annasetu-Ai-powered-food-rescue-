"""Surplus Food Donation Domain Service."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid
from app.db.supabase import SupabaseClient
from app.schemas.donation import DonationCreate, DonationResponse, DonationStatus, DonationUpdate
from app.schemas.need import DietType
from app.services.audit_service import AuditService
from app.utils.exceptions import ForbiddenException, NotFoundException, ValidationException


class DonationService:
    """Service managing surplus food donations."""

    MIN_DONATION_KG = 5.0

    def __init__(self, db: SupabaseClient):
        self.db = db
        self.audit = AuditService(db)

    async def _verify_location_ownership(self, location_id: str, donor_id: str):
        location = await self.db.get_by_id("locations", location_id, id_column="id")
        if not location:
            raise NotFoundException("Pickup location not found.", error_code="LOCATION_NOT_FOUND")
        if location.get("user_id") != donor_id:
            raise ForbiddenException("Pickup location does not belong to your account.", error_code="LOCATION_FORBIDDEN")

    async def _verify_food_category_compatibility(self, food_category_id: str, donation_diet: DietType):
        category = await self.db.get_by_id("food_categories", food_category_id, id_column="id")
        if not category:
            raise NotFoundException("Specified food category not found.", error_code="CATEGORY_NOT_FOUND")
        if not category.get("is_active", True):
            raise ValidationException("Specified food category is currently inactive.", error_code="CATEGORY_INACTIVE")

        cat_diet = category.get("diet_type")
        if cat_diet and cat_diet.upper() != "MIXED" and donation_diet != DietType.MIXED:
            # If category has specific diet (e.g. VEGETARIAN) and donation is NON_VEGETARIAN -> conflict
            if cat_diet.upper() != donation_diet.value:
                raise ValidationException(
                    f"Donation diet type '{donation_diet.value}' is incompatible with category diet '{cat_diet}'.",
                    error_code="DIET_INCOMPATIBLE",
                )

    async def create_donation(self, donor_id: str, payload: DonationCreate) -> DonationResponse:
        """Create a new surplus food donation in DRAFT status."""
        if payload.declared_quantity_kg < self.MIN_DONATION_KG:
            raise ValidationException(
                f"Donation quantity must be at least {self.MIN_DONATION_KG} kg.",
                error_code="MINIMUM_QUANTITY_NOT_MET",
            )

        # 1. Verify pickup location ownership
        await self._verify_location_ownership(payload.pickup_location_id, donor_id)

        # 2. Verify food category exists and is diet-compatible
        await self._verify_food_category_compatibility(payload.food_category_id, payload.diet_type)

        donation_id = str(uuid.uuid4())
        donation_record = {
            "id": donation_id,
            "donor_id": donor_id,
            "diet_type": payload.diet_type.value,
            "food_category_id": payload.food_category_id,
            "declared_quantity_kg": payload.declared_quantity_kg,
            "remaining_quantity_kg": payload.declared_quantity_kg,
            "preparation_at": payload.preparation_at,
            "available_from": payload.available_from,
            "rescue_deadline": payload.rescue_deadline,
            "storage_condition": payload.storage_condition.value,
            "packaging_type": payload.packaging_type,
            "allergen_information": payload.allergen_information,
            "raw_description": payload.raw_description,
            "normalized_description": payload.normalized_description,
            "image_path": payload.image_path,
            "pickup_location_id": payload.pickup_location_id,
            "status": DonationStatus.DRAFT.value,
        }

        created = await self.db.insert("donations", donation_record)
        await self.audit.log_event("DONATION_CREATED", "donations", donation_id, user_id=donor_id, new_values=donation_record)
        return DonationResponse(**created)

    async def list_donations(self, donor_id: str, status: Optional[DonationStatus] = None) -> List[DonationResponse]:
        """List donations created by the donor."""
        params = {"donor_id": f"eq.{donor_id}"}
        if status:
            params["status"] = f"eq.{status.value}"

        records = await self.db.query("donations", params=params, order="created_at.desc")
        return [DonationResponse(**r) for r in records]

    async def get_donation(self, donation_id: str, donor_id: Optional[str] = None) -> DonationResponse:
        """Get donation by ID with optional donor ownership enforcement."""
        record = await self.db.get_by_id("donations", donation_id, id_column="id")
        if not record:
            raise NotFoundException("Donation record not found.", error_code="DONATION_NOT_FOUND")

        if donor_id and record.get("donor_id") != donor_id:
            raise ForbiddenException("Access forbidden. You do not own this donation.", error_code="DONATION_FORBIDDEN")

        return DonationResponse(**record)

    async def update_donation(self, donation_id: str, donor_id: str, payload: DonationUpdate) -> DonationResponse:
        """Update draft or posted donation details."""
        existing = await self.get_donation(donation_id, donor_id=donor_id)

        if existing.status not in (DonationStatus.DRAFT, DonationStatus.POSTED):
            raise ValidationException(
                f"Cannot modify donation in status '{existing.status.value}'.",
                error_code="DONATION_IMMUTABLE",
            )

        fields: Dict[str, Any] = {}
        target_diet = payload.diet_type or existing.diet_type
        target_category_id = payload.food_category_id or existing.food_category_id

        if payload.food_category_id or payload.diet_type:
            await self._verify_food_category_compatibility(target_category_id, target_diet)

        if payload.diet_type is not None:
            fields["diet_type"] = payload.diet_type.value
        if payload.food_category_id is not None:
            fields["food_category_id"] = payload.food_category_id
        if payload.declared_quantity_kg is not None:
            if payload.declared_quantity_kg < self.MIN_DONATION_KG:
                raise ValidationException(f"Declared quantity must be at least {self.MIN_DONATION_KG} kg.")
            fields["declared_quantity_kg"] = payload.declared_quantity_kg
            if existing.status == DonationStatus.DRAFT:
                fields["remaining_quantity_kg"] = payload.declared_quantity_kg
        if payload.preparation_at is not None:
            fields["preparation_at"] = payload.preparation_at
        if payload.available_from is not None:
            fields["available_from"] = payload.available_from
        if payload.rescue_deadline is not None:
            fields["rescue_deadline"] = payload.rescue_deadline
        if payload.storage_condition is not None:
            fields["storage_condition"] = payload.storage_condition.value
        if payload.packaging_type is not None:
            fields["packaging_type"] = payload.packaging_type
        if payload.allergen_information is not None:
            fields["allergen_information"] = payload.allergen_information
        if payload.raw_description is not None:
            fields["raw_description"] = payload.raw_description
        if payload.normalized_description is not None:
            fields["normalized_description"] = payload.normalized_description
        if payload.image_path is not None:
            fields["image_path"] = payload.image_path
        if payload.pickup_location_id is not None:
            await self._verify_location_ownership(payload.pickup_location_id, donor_id)
            fields["pickup_location_id"] = payload.pickup_location_id

        # Timeline validation
        avail = fields.get("available_from", existing.available_from)
        deadline = fields.get("rescue_deadline", existing.rescue_deadline)
        if deadline <= avail:
            raise ValidationException("rescue_deadline must be after available_from.")

        if not fields:
            return existing

        updated = await self.db.update_by_id("donations", donation_id, fields, id_column="id")
        return DonationResponse(**updated)

    async def post_donation(self, donation_id: str, donor_id: str) -> DonationResponse:
        """Publish donation to POSTED state making it eligible for matching."""
        existing = await self.get_donation(donation_id, donor_id=donor_id)

        if existing.status == DonationStatus.POSTED:
            return existing

        if existing.status != DonationStatus.DRAFT:
            raise ValidationException(
                f"Cannot post donation in status '{existing.status.value}'.",
                error_code="INVALID_STATUS_TRANSITION",
            )

        # Check rescue_deadline is in the future
        try:
            deadline = datetime.fromisoformat(existing.rescue_deadline.replace("Z", "+00:00"))
            now = datetime.now(timezone.utc)
            if deadline <= now:
                raise ValidationException(
                    "Rescue deadline must be strictly in the future to post donation.",
                    error_code="DEADLINE_IN_PAST",
                )
        except (ValueError, TypeError):
            pass

        updated = await self.db.update_by_id("donations", donation_id, {"status": DonationStatus.POSTED.value}, id_column="id")
        await self.audit.log_event("DONATION_POSTED", "donations", donation_id, user_id=donor_id, old_values={"status": existing.status.value}, new_values={"status": DonationStatus.POSTED.value})
        return DonationResponse(**updated)

    async def cancel_donation(self, donation_id: str, donor_id: str) -> DonationResponse:
        """Cancel a donation."""
        existing = await self.get_donation(donation_id, donor_id=donor_id)

        if existing.status in (DonationStatus.CANCELLED, DonationStatus.ALLOCATED):
            return existing

        updated = await self.db.update_by_id("donations", donation_id, {"status": DonationStatus.CANCELLED.value}, id_column="id")
        await self.audit.log_event("DONATION_CANCELLED", "donations", donation_id, user_id=donor_id, old_values={"status": existing.status.value}, new_values={"status": DonationStatus.CANCELLED.value})
        return DonationResponse(**updated)
