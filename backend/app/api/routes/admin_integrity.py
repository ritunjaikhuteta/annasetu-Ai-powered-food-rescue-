"""Admin Food Integrity Review Queue Routes."""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from app.api.deps import get_integrity_service, require_admin
from app.schemas.auth import ProfileResponse
from app.schemas.integrity import (
    FoodIntegrityCheckResponse,
    ManualReviewRequest,
    ManualReviewStatus,
)
from app.services.integrity_service import IntegrityService
from app.utils.exceptions import NotFoundException

router = APIRouter(prefix="/admin/integrity", tags=["Admin Integrity Reviews"])


@router.get(
    "/reviews",
    response_model=List[FoodIntegrityCheckResponse],
    summary="List Food Integrity Discrepancies",
    description="Retrieves package visual consistency and seal discrepancies pending manual review.",
)
async def list_integrity_reviews(
    status: Optional[ManualReviewStatus] = Query(default=None),
    current_admin: ProfileResponse = Depends(require_admin),
    service: IntegrityService = Depends(get_integrity_service),
) -> List[FoodIntegrityCheckResponse]:
    return await service.list_reviews(status=status)


@router.get(
    "/{check_id}",
    response_model=FoodIntegrityCheckResponse,
    summary="Get Integrity Check Detail",
    description="Retrieves full side-by-side evidence, seal status, and AI visual signal for a package check.",
)
async def get_integrity_check_detail(
    check_id: str,
    current_admin: ProfileResponse = Depends(require_admin),
    service: IntegrityService = Depends(get_integrity_service),
) -> FoodIntegrityCheckResponse:
    record = await service.db.get_by_id("food_integrity_checks", check_id)
    if not record:
        raise NotFoundException(f"Integrity check {check_id} not found.")
    return FoodIntegrityCheckResponse(**record)


@router.post(
    "/{check_id}/review",
    response_model=FoodIntegrityCheckResponse,
    summary="Submit Integrity Review Decision",
    description="Admin decision on package discrepancy: CLEARED, REQUIRES_ACTION, or DISPUTED with review notes.",
)
async def submit_integrity_review(
    check_id: str,
    payload: ManualReviewRequest,
    current_admin: ProfileResponse = Depends(require_admin),
    service: IntegrityService = Depends(get_integrity_service),
) -> FoodIntegrityCheckResponse:
    return await service.submit_review(
        check_id=check_id,
        reviewer_id=current_admin.id,
        payload=payload,
    )
