"""Donor Domain Service."""

from typing import Any, Dict
from app.db.supabase import SupabaseClient
from app.schemas.common import VerificationStatus
from app.schemas.donor import DonorProfileResponse, DonorProfileUpdate
from app.utils.exceptions import NotFoundException


class DonorService:
    """Service managing donor business profiles and domain logic."""

    def __init__(self, db: SupabaseClient):
        self.db = db

    async def get_donor_profile(self, user_id: str) -> DonorProfileResponse:
        record = await self.db.get_by_id("donor_profiles", user_id, id_column="user_id")
        if not record:
            raise NotFoundException("Donor profile record not found.", error_code="DONOR_PROFILE_NOT_FOUND")

        raw_status = (record.get("verification_status") or "PENDING").upper()
        try:
            status = VerificationStatus(raw_status)
        except ValueError:
            status = VerificationStatus.PENDING

        return DonorProfileResponse(
            id=record["id"],
            user_id=record["user_id"],
            business_name=record.get("business_name", ""),
            business_type=record.get("business_type"),
            fssai_license_number=record.get("fssai_license_number"),
            gstin=record.get("gstin"),
            contact_person_name=record.get("contact_person_name"),
            pickup_instructions=record.get("pickup_instructions"),
            operating_hours=record.get("operating_hours"),
            verification_status=status,
            subscription_plan=record.get("subscription_plan", "FREE"),
            created_at=str(record.get("created_at")) if record.get("created_at") else None,
            updated_at=str(record.get("updated_at")) if record.get("updated_at") else None,
        )

    async def update_donor_profile(self, user_id: str, payload: DonorProfileUpdate) -> DonorProfileResponse:
        """Update donor profile with whitelist filtering to block verification_status and subscription tampering."""
        fields_to_update: Dict[str, Any] = {}
        if payload.business_name is not None:
            fields_to_update["business_name"] = payload.business_name.strip()
        if payload.business_type is not None:
            fields_to_update["business_type"] = payload.business_type.strip()
        if payload.fssai_license_number is not None:
            fields_to_update["fssai_license_number"] = payload.fssai_license_number.strip()
        if payload.gstin is not None:
            fields_to_update["gstin"] = payload.gstin.strip()
        if payload.contact_person_name is not None:
            fields_to_update["contact_person_name"] = payload.contact_person_name.strip()
        if payload.pickup_instructions is not None:
            fields_to_update["pickup_instructions"] = payload.pickup_instructions.strip()
        if payload.operating_hours is not None:
            fields_to_update["operating_hours"] = payload.operating_hours

        if not fields_to_update:
            return await self.get_donor_profile(user_id)

        # Update in donor_profiles by user_id
        await self.db.update_by_id("donor_profiles", user_id, fields_to_update, id_column="user_id")
        return await self.get_donor_profile(user_id)
