"""Self-service user profile routes."""

from fastapi import APIRouter, Depends
from app.api.deps import get_current_user, get_profile_service
from app.schemas.auth import AuthenticatedUser, ProfileResponse, ProfileUpdate
from app.services.profile_service import ProfileService

router = APIRouter(prefix="/me", tags=["Profiles"])


@router.get(
    "/profile",
    response_model=ProfileResponse,
    summary="Get My Profile",
    description="Fetches the current user's profile from public.profiles.",
)
async def get_my_profile(
    user: AuthenticatedUser = Depends(get_current_user),
    profile_service: ProfileService = Depends(get_profile_service),
) -> ProfileResponse:
    return await profile_service.get_user_profile(user.id)


@router.patch(
    "/profile",
    response_model=ProfileResponse,
    summary="Update My Profile",
    description="Updates editable profile fields (full_name, phone). System-managed fields (role, is_active) cannot be altered.",
)
async def update_my_profile(
    payload: ProfileUpdate,
    user: AuthenticatedUser = Depends(get_current_user),
    profile_service: ProfileService = Depends(get_profile_service),
) -> ProfileResponse:
    return await profile_service.update_user_profile(user.id, payload)
