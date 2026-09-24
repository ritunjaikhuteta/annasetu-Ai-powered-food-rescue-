"""User identity and authorization status routes."""

from fastapi import APIRouter, Depends
from app.api.deps import get_auth_service, get_current_user
from app.schemas.auth import AuthenticatedUser, MeResponse
from app.services.auth_service import AuthService

router = APIRouter(tags=["Authentication"])


@router.get(
    "/me",
    response_model=MeResponse,
    summary="Get Current User Identity and Authoritative Profile",
    description="Returns the authenticated Supabase user, authoritative database role, profile record, and verification gating status.",
)
async def get_me(
    user: AuthenticatedUser = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
) -> MeResponse:
    return await auth_service.get_me_details(user)
