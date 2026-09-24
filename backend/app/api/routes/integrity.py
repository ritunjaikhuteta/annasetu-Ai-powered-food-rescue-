"""Food Integrity and Operational Manual Review API Endpoints."""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from app.api.deps import (
    get_integrity_service,
    require_admin,
    require_role,
)
from app.schemas.common import UserRole
from app.schemas.integrity import (
    FoodIntegrityCheckResponse,
    ManualReviewRequest,
    ManualReviewStatus,
)
from app.schemas.auth import ProfileResponse
from app.services.integrity_service import IntegrityService

router = APIRouter(prefix="/integrity", tags=["Food Integrity & Review"])


@router.get(
    "/reviews",
    response_model=List[FoodIntegrityCheckResponse],
    summary="List Food Integrity Checks for Review",
    description="Admin endpoint to retrieve package integrity checks requiring operational review.",
)
async def list_integrity_reviews(
    status: Optional[ManualReviewStatus] = Query(default=None, description="Filter by review status."),
    current_admin: ProfileResponse = Depends(require_admin),
    integrity_service: IntegrityService = Depends(get_integrity_service),
) -> List[FoodIntegrityCheckResponse]:
    return await integrity_service.list_reviews(status=status)


@router.post(
    "/{check_id}/review",
    response_model=FoodIntegrityCheckResponse,
    summary="Submit Manual Review Outcome",
    description="Admin reviews and clears or escalates an integrity check.",
)
async def submit_manual_review(
    check_id: str,
    payload: ManualReviewRequest,
    current_admin: ProfileResponse = Depends(require_admin),
    integrity_service: IntegrityService = Depends(get_integrity_service),
) -> FoodIntegrityCheckResponse:
    return await integrity_service.submit_review(
        check_id=check_id,
        reviewer_id=current_admin.id,
        payload=payload,
    )


@router.get(
    "/deliveries/{delivery_id}",
    response_model=List[FoodIntegrityCheckResponse],
    summary="Get Integrity Checks for Delivery",
    description="Retrieves package visual consistency checks associated with a delivery.",
)
async def get_delivery_integrity_checks(
    delivery_id: str,
    current_profile: ProfileResponse = Depends(require_role(UserRole.DONOR, UserRole.RECEIVER, UserRole.DRIVER, UserRole.ADMIN)),
    integrity_service: IntegrityService = Depends(get_integrity_service),
) -> List[FoodIntegrityCheckResponse]:
    records = await integrity_service.db.query("food_integrity_checks", params={"delivery_id": f"eq.{delivery_id}"})
    return [FoodIntegrityCheckResponse(**r) for r in records]
