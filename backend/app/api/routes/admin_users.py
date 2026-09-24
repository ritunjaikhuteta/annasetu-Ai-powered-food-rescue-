"""Admin User Directory and Operational Driver Directory Routes."""

from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, Query
from app.api.deps import get_admin_operations_service, require_admin
from app.schemas.admin import PaginatedResponse
from app.schemas.admin_operations import AdminUserItem, UserActionRequest
from app.schemas.auth import ProfileResponse
from app.services.admin_operations_service import AdminOperationsService

router = APIRouter(prefix="/admin", tags=["Admin Users & Drivers"])


@router.get(
    "/users",
    response_model=PaginatedResponse[AdminUserItem],
    summary="List User Directory",
    description="Administrative user directory supporting search, role, active, and verification status filters.",
)
async def list_users(
    role: Optional[str] = Query(default=None),
    verification_status: Optional[str] = Query(default=None),
    is_active: Optional[bool] = Query(default=None),
    search: Optional[str] = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_admin: ProfileResponse = Depends(require_admin),
    service: AdminOperationsService = Depends(get_admin_operations_service),
) -> PaginatedResponse[AdminUserItem]:
    return await service.list_users(
        role=role,
        verification_status=verification_status,
        is_active=is_active,
        search=search,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/users/{user_id}",
    response_model=Dict[str, Any],
    summary="Get User Detail",
    description="Retrieves user profile, role profile, and verification documentation records.",
)
async def get_user_detail(
    user_id: str,
    current_admin: ProfileResponse = Depends(require_admin),
    service: AdminOperationsService = Depends(get_admin_operations_service),
) -> Dict[str, Any]:
    return await service.get_user_detail(user_id)


@router.post(
    "/users/{user_id}/activate",
    response_model=Dict[str, Any],
    summary="Activate User Account",
    description="Reactivates an active user account. Never modifies profile.role.",
)
async def activate_user(
    user_id: str,
    payload: UserActionRequest,
    current_admin: ProfileResponse = Depends(require_admin),
    service: AdminOperationsService = Depends(get_admin_operations_service),
) -> Dict[str, Any]:
    return await service.activate_user(user_id=user_id, admin_id=current_admin.id, reason=payload.reason)


@router.post(
    "/users/{user_id}/deactivate",
    response_model=Dict[str, Any],
    summary="Deactivate User Account",
    description="Suspends or deactivates a user account with required reason. Never modifies profile.role.",
)
async def deactivate_user(
    user_id: str,
    payload: UserActionRequest,
    current_admin: ProfileResponse = Depends(require_admin),
    service: AdminOperationsService = Depends(get_admin_operations_service),
) -> Dict[str, Any]:
    return await service.deactivate_user(user_id=user_id, admin_id=current_admin.id, reason=payload.reason)


@router.get(
    "/drivers",
    response_model=PaginatedResponse[Dict[str, Any]],
    summary="List Driver Operations Directory",
    description="Administrative driver partner directory with vehicle specs, status, and verification state.",
)
async def list_drivers(
    verification_status: Optional[str] = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_admin: ProfileResponse = Depends(require_admin),
    service: AdminOperationsService = Depends(get_admin_operations_service),
) -> PaginatedResponse[Dict[str, Any]]:
    return await service.list_drivers(verification_status=verification_status, page=page, page_size=page_size)
