"""General Profile Service."""

from typing import Any, Dict
from app.db.supabase import SupabaseClient
from app.schemas.auth import ProfileResponse, ProfileUpdate
from app.schemas.common import UserRole
from app.utils.exceptions import AppException, NotFoundException


class ProfileService:
    """Service managing public.profiles records."""

    def __init__(self, db: SupabaseClient):
        self.db = db

    async def get_user_profile(self, user_id: str) -> ProfileResponse:
        record = await self.db.get_by_id("profiles", user_id, id_column="id")
        if not record:
            raise NotFoundException("User profile not found.", error_code="PROFILE_NOT_FOUND")

        return ProfileResponse(
            id=record["id"],
            full_name=record.get("full_name"),
            phone=record.get("phone"),
            role=UserRole(record["role"].upper()),
            is_active=record.get("is_active", True),
            created_at=str(record.get("created_at")) if record.get("created_at") else None,
            updated_at=str(record.get("updated_at")) if record.get("updated_at") else None,
        )

    async def update_user_profile(self, user_id: str, payload: ProfileUpdate) -> ProfileResponse:
        """Update user profile while ensuring protected fields cannot be tampered with."""
        data_to_update: Dict[str, Any] = {}
        if payload.full_name is not None:
            data_to_update["full_name"] = payload.full_name.strip()
        if payload.phone is not None:
            data_to_update["phone"] = payload.phone.strip()

        if not data_to_update:
            return await self.get_user_profile(user_id)

        updated_record = await self.db.update_by_id("profiles", user_id, data_to_update, id_column="id")
        return ProfileResponse(
            id=updated_record["id"],
            full_name=updated_record.get("full_name"),
            phone=updated_record.get("phone"),
            role=UserRole(updated_record["role"].upper()),
            is_active=updated_record.get("is_active", True),
            created_at=str(updated_record.get("created_at")) if updated_record.get("created_at") else None,
            updated_at=str(updated_record.get("updated_at")) if updated_record.get("updated_at") else None,
        )
