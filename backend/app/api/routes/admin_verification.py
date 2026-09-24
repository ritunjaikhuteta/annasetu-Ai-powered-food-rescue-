"""Admin Verification Queue & Review Decision Routes."""

from typing import Optional
from fastapi import APIRouter, Depends, Query
from app.api.deps import get_admin_verification_service, require_admin
from app.schemas.admin import PaginatedResponse
from app.schemas.admin_verification import (
    VerificationApproveRequest,
    VerificationDetailResponse,
    VerificationItemResponse,
    VerificationRejectRequest,
    VerificationRequestReviewRequest,
)
from app.schemas.auth import ProfileResponse
from app.services.admin_verification_service import AdminVerificationService

router = APIRouter(prefix="/admin/verifications", tags=["Admin Verification Queue"])


@router.get(
    "",
    response_model=PaginatedResponse[VerificationItemResponse],
    summary="List Verification Queue",
    description="Retrieves pending and under-review verification records ordered oldest first.",
)
async def list_verifications(
    role: Optional[str] = Query(default=None, description="Filter by role: DONOR, RECEIVER, DRIVER."),
    verification_type: Optional[str] = Query(default=None, description="Filter by verification type."),
    status: Optional[str] = Query(default=None, description="Filter by status: PENDING, UNDER_REVIEW, VERIFIED, REJECTED."),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_admin: ProfileResponse = Depends(require_admin),
    service: AdminVerificationService = Depends(get_admin_verification_service),
) -> PaginatedResponse[VerificationItemResponse]:
    return await service.list_verifications(
        role=role,
        verification_type=verification_type,
        status=status,
        page=page,
        page_size=page_size,
    )


@router.get(
    "/{verification_id}",
    response_model=VerificationDetailResponse,
    summary="Get Verification Case Details",
    description="Retrieves submitted documents, extracted OCR candidate fields, and profile details for review.",
)
async def get_verification_detail(
    verification_id: str,
    current_admin: ProfileResponse = Depends(require_admin),
    service: AdminVerificationService = Depends(get_admin_verification_service),
) -> VerificationDetailResponse:
    return await service.get_verification_detail(verification_id)


@router.post(
    "/{verification_id}/approve",
    response_model=VerificationDetailResponse,
    summary="Approve Verification Case",
    description="Explicit human admin approval. Sets record and profile status to VERIFIED.",
)
async def approve_verification(
    verification_id: str,
    payload: Optional[VerificationApproveRequest] = None,
    current_admin: ProfileResponse = Depends(require_admin),
    service: AdminVerificationService = Depends(get_admin_verification_service),
) -> VerificationDetailResponse:
    return await service.approve_verification(
        verification_id=verification_id,
        admin_id=current_admin.id,
        payload=payload,
    )


@router.post(
    "/{verification_id}/reject",
    response_model=VerificationDetailResponse,
    summary="Reject Verification Case",
    description="Explicit human admin rejection. Requires documented rejection reason.",
)
async def reject_verification(
    verification_id: str,
    payload: VerificationRejectRequest,
    current_admin: ProfileResponse = Depends(require_admin),
    service: AdminVerificationService = Depends(get_admin_verification_service),
) -> VerificationDetailResponse:
    return await service.reject_verification(
        verification_id=verification_id,
        admin_id=current_admin.id,
        payload=payload,
    )


@router.post(
    "/{verification_id}/request-review",
    response_model=VerificationDetailResponse,
    summary="Request Manual Review Escalation",
    description="Places verification into UNDER_REVIEW state with operational notes.",
)
async def request_review(
    verification_id: str,
    payload: VerificationRequestReviewRequest,
    current_admin: ProfileResponse = Depends(require_admin),
    service: AdminVerificationService = Depends(get_admin_verification_service),
) -> VerificationDetailResponse:
    return await service.request_review(
        verification_id=verification_id,
        admin_id=current_admin.id,
        payload=payload,
    )
