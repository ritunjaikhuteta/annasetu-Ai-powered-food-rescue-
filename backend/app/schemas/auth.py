"""Authentication and Session Schemas."""

from typing import Any, Dict, Optional
from pydantic import BaseModel, EmailStr, Field
from app.schemas.common import UserRole, VerificationStatus


class AuthenticatedUser(BaseModel):
    """Represents authenticated user identity from Supabase Auth."""

    id: str = Field(..., description="Supabase auth UUID")
    email: Optional[str] = None
    phone: Optional[str] = None
    app_metadata: Dict[str, Any] = Field(default_factory=dict)
    user_metadata: Dict[str, Any] = Field(default_factory=dict)


class ProfileResponse(BaseModel):
    """Authoritative user profile from public.profiles."""

    id: str
    full_name: Optional[str] = None
    phone: Optional[str] = None
    role: UserRole
    is_active: bool = True
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class ProfileUpdate(BaseModel):
    """Allowed self-service profile update fields.
    Note: role, is_active, and verification_status are strictly disallowed.
    """

    full_name: Optional[str] = Field(None, min_length=1, max_length=150)
    phone: Optional[str] = Field(None, min_length=7, max_length=20)


class MeResponse(BaseModel):
    """Comprehensive identity and authorization state returned by /api/v1/me."""

    user: AuthenticatedUser
    role: UserRole
    profile: ProfileResponse
    verification_status: VerificationStatus
    is_verified: bool
