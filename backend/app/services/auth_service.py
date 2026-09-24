"""Authentication and Authorization Service."""

import logging
from typing import Any, Dict, Optional, Tuple
from app.db.supabase import SupabaseClient
from app.schemas.auth import AuthenticatedUser, MeResponse, ProfileResponse
from app.schemas.common import UserRole, VerificationStatus
from app.utils.exceptions import ForbiddenException, NotFoundException, UnauthorizedException

logger = logging.getLogger("annasetu.services.auth")


class AuthService:
    """Service handling profile lookups, verification status, and authoritative role checks."""

    def __init__(self, db: SupabaseClient):
        self.db = db

    async def get_profile(self, user_id: str) -> ProfileResponse:
        """Fetch authoritative profile from public.profiles for the given user ID."""
        record = await self.db.get_by_id("profiles", user_id, id_column="id")
        if not record:
            raise NotFoundException(
                message="User profile not found. Complete your registration or contact support.",
                error_code="PROFILE_NOT_FOUND",
            )

        if not record.get("is_active", True):
            raise ForbiddenException(
                message="Your account has been deactivated. Please contact support.",
                error_code="ACCOUNT_DEACTIVATED",
            )

        try:
            role = UserRole(record["role"].upper())
        except (KeyError, ValueError):
            raise ForbiddenException(
                message="User role is invalid or not recognized.",
                error_code="INVALID_ROLE",
            )

        return ProfileResponse(
            id=record["id"],
            full_name=record.get("full_name"),
            phone=record.get("phone"),
            role=role,
            is_active=record.get("is_active", True),
            created_at=str(record.get("created_at")) if record.get("created_at") else None,
            updated_at=str(record.get("updated_at")) if record.get("updated_at") else None,
        )

    async def get_verification_status(self, user_id: str, role: UserRole) -> VerificationStatus:
        """Query role-specific profile to determine current verification status."""
        table_map = {
            UserRole.DONOR: "donor_profiles",
            UserRole.RECEIVER: "receiver_profiles",
            UserRole.DRIVER: "driver_profiles",
        }

        table_name = table_map.get(role)
        if not table_name:
            # ADMIN role or others default to VERIFIED or system managed
            return VerificationStatus.VERIFIED

        role_record = await self.db.get_by_id(table_name, user_id, id_column="user_id")
        if not role_record:
            return VerificationStatus.PENDING

        raw_status = (role_record.get("verification_status") or "PENDING").upper()
        try:
            return VerificationStatus(raw_status)
        except ValueError:
            return VerificationStatus.PENDING

    async def get_me_details(self, user: AuthenticatedUser) -> MeResponse:
        """Fetch full identity, profile, and verification state for /api/v1/me."""
        profile = await self.get_profile(user.id)
        status = await self.get_verification_status(user.id, profile.role)

        return MeResponse(
            user=user,
            role=profile.role,
            profile=profile,
            verification_status=status,
            is_verified=(status == VerificationStatus.VERIFIED),
        )
