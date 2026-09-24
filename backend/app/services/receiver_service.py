"""Receiver (NGO) Domain Service."""

from typing import Any, Dict
from app.db.supabase import SupabaseClient
from app.schemas.common import VerificationStatus
from app.schemas.receiver import ReceiverProfileResponse, ReceiverProfileUpdate
from app.utils.exceptions import NotFoundException


class ReceiverService:
    """Service managing receiver NGO profiles and domain logic."""

    def __init__(self, db: SupabaseClient):
        self.db = db

    async def get_receiver_profile(self, user_id: str) -> ReceiverProfileResponse:
        record = await self.db.get_by_id("receiver_profiles", user_id, id_column="user_id")
        if not record:
            raise NotFoundException("Receiver profile record not found.", error_code="RECEIVER_PROFILE_NOT_FOUND")

        raw_status = (record.get("verification_status") or "PENDING").upper()
        try:
            status = VerificationStatus(raw_status)
        except ValueError:
            status = VerificationStatus.PENDING

        return ReceiverProfileResponse(
            id=record["id"],
            user_id=record["user_id"],
            organization_name=record.get("organization_name", ""),
            organization_type=record.get("organization_type"),
            registration_number=record.get("registration_number"),
            darpan_id=record.get("darpan_id"),
            pan_number=record.get("pan_number"),
            contact_person_name=record.get("contact_person_name"),
            beneficiary_count=record.get("beneficiary_count"),
            storage_capacity_liters=record.get("storage_capacity_liters"),
            has_refrigeration=record.get("has_refrigeration", False),
            operating_hours=record.get("operating_hours"),
            verification_status=status,
            created_at=str(record.get("created_at")) if record.get("created_at") else None,
            updated_at=str(record.get("updated_at")) if record.get("updated_at") else None,
        )

    async def update_receiver_profile(self, user_id: str, payload: ReceiverProfileUpdate) -> ReceiverProfileResponse:
        """Update receiver profile while strictly protecting verification_status."""
        fields_to_update: Dict[str, Any] = {}
        if payload.organization_name is not None:
            fields_to_update["organization_name"] = payload.organization_name.strip()
        if payload.organization_type is not None:
            fields_to_update["organization_type"] = payload.organization_type.strip()
        if payload.registration_number is not None:
            fields_to_update["registration_number"] = payload.registration_number.strip()
        if payload.darpan_id is not None:
            fields_to_update["darpan_id"] = payload.darpan_id.strip()
        if payload.pan_number is not None:
            fields_to_update["pan_number"] = payload.pan_number.strip()
        if payload.contact_person_name is not None:
            fields_to_update["contact_person_name"] = payload.contact_person_name.strip()
        if payload.beneficiary_count is not None:
            fields_to_update["beneficiary_count"] = payload.beneficiary_count
        if payload.storage_capacity_liters is not None:
            fields_to_update["storage_capacity_liters"] = payload.storage_capacity_liters
        if payload.has_refrigeration is not None:
            fields_to_update["has_refrigeration"] = payload.has_refrigeration
        if payload.operating_hours is not None:
            fields_to_update["operating_hours"] = payload.operating_hours

        if not fields_to_update:
            return await self.get_receiver_profile(user_id)

        await self.db.update_by_id("receiver_profiles", user_id, fields_to_update, id_column="user_id")
        return await self.get_receiver_profile(user_id)
