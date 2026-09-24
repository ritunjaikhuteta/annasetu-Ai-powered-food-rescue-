"""Core Authentication, Profile, and Role Dependencies."""

from typing import Callable, List, Optional
from fastapi import Depends, Header, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from app.core.security import verify_supabase_token
from app.db.supabase import SupabaseClient, get_supabase_client
from app.schemas.auth import AuthenticatedUser, ProfileResponse
from app.schemas.common import UserRole, VerificationStatus
from app.services.auth_service import AuthService
from app.utils.exceptions import ForbiddenException, UnauthorizedException, VerificationRequiredException

security_bearer = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Security(security_bearer),
    db: SupabaseClient = Depends(get_supabase_client),
) -> AuthenticatedUser:
    """Dependency that extracts and validates the Supabase JWT Bearer token."""
    if not credentials or not credentials.credentials:
        raise UnauthorizedException(
            message="Authentication credentials were not provided. Include 'Authorization: Bearer <token>' header.",
            error_code="UNAUTHORIZED",
        )

    return await verify_supabase_token(credentials.credentials, db_client=db)


async def get_auth_service(
    db: SupabaseClient = Depends(get_supabase_client),
) -> AuthService:
    """Dependency for AuthService."""
    return AuthService(db)


async def get_current_profile(
    user: AuthenticatedUser = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
) -> ProfileResponse:
    """Dependency retrieving the authoritative profile for the authenticated user."""
    return await auth_service.get_profile(user.id)


def require_role(*allowed_roles: UserRole) -> Callable:
    """Factory creating a dependency that enforces the user has one of the allowed roles."""
    async def role_checker(
        profile: ProfileResponse = Depends(get_current_profile),
    ) -> ProfileResponse:
        if profile.role not in allowed_roles:
            role_names = ", ".join(r.value for r in allowed_roles)
            raise ForbiddenException(
                message=f"Access forbidden. Resource requires one of [{role_names}] roles, but your profile role is {profile.role.value}.",
                error_code="INSUFFICIENT_ROLE",
                details={"required_roles": [r.value for r in allowed_roles], "user_role": profile.role.value},
            )
        return profile

    return role_checker


# Public role dependencies
require_donor = require_role(UserRole.DONOR)
require_receiver = require_role(UserRole.RECEIVER)
require_driver = require_role(UserRole.DRIVER)
require_admin = require_role(UserRole.ADMIN)


def require_verified_role(role: UserRole) -> Callable:
    """Factory creating a dependency that enforces role + VERIFIED verification status."""
    async def verified_checker(
        profile: ProfileResponse = Depends(get_current_profile),
        auth_service: AuthService = Depends(get_auth_service),
    ) -> ProfileResponse:
        if profile.role != role:
            raise ForbiddenException(
                message=f"Access forbidden. Required role {role.value}, your role is {profile.role.value}.",
                error_code="INSUFFICIENT_ROLE",
            )

        status = await auth_service.get_verification_status(profile.id, role)
        if status != VerificationStatus.VERIFIED:
            raise VerificationRequiredException(
                message=f"Your {role.value} account verification status is '{status.value}'. Operational action requires 'VERIFIED' status.",
                details={"current_status": status.value, "required_status": VerificationStatus.VERIFIED.value},
            )

        return profile

    return verified_checker


require_verified_donor = require_verified_role(UserRole.DONOR)
require_verified_receiver = require_verified_role(UserRole.RECEIVER)
require_verified_driver = require_verified_role(UserRole.DRIVER)
