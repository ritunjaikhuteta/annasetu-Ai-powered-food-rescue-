"""Donor Surplus Food Donation Routes."""

from typing import List, Optional
from fastapi import APIRouter, Depends, status
from app.ai.schemas import FoodQualityAssessment, FoodQualityCheckRequest
from app.ai.service import AIService
from app.api.deps import get_ai_service, get_donation_service, require_donor
from app.core.dependencies import get_current_profile
from app.schemas.auth import ProfileResponse
from app.schemas.donation import DonationCreate, DonationResponse, DonationStatus, DonationUpdate
from app.services.donation_service import DonationService

router = APIRouter(prefix="/donations", tags=["Donations"])


@router.post(
    "",
    response_model=DonationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a Surplus Food Donation",
    description="Registers a new surplus food donation in DRAFT status. Minimum 5 kg declared quantity enforced. Enforces role = DONOR.",
)
async def create_donation(
    payload: DonationCreate,
    donor_profile: ProfileResponse = Depends(require_donor),
    donation_service: DonationService = Depends(get_donation_service),
) -> DonationResponse:
    return await donation_service.create_donation(donor_profile.id, payload)


@router.get(
    "",
    response_model=List[DonationResponse],
    summary="List My Donations",
    description="Retrieves all surplus food donations created by the authenticated donor.",
)
async def list_donations(
    status_filter: Optional[DonationStatus] = None,
    donor_profile: ProfileResponse = Depends(require_donor),
    donation_service: DonationService = Depends(get_donation_service),
) -> List[DonationResponse]:
    return await donation_service.list_donations(donor_profile.id, status=status_filter)


@router.get(
    "/{donation_id}",
    response_model=DonationResponse,
    summary="Get Donation Details",
    description="Retrieves details of a specific surplus donation owned by the donor.",
)
async def get_donation(
    donation_id: str,
    donor_profile: ProfileResponse = Depends(require_donor),
    donation_service: DonationService = Depends(get_donation_service),
) -> DonationResponse:
    return await donation_service.get_donation(donation_id, donor_id=donor_profile.id)


@router.patch(
    "/{donation_id}",
    response_model=DonationResponse,
    summary="Update Donation Details",
    description="Updates editable donation details while in DRAFT or POSTED status.",
)
async def update_donation(
    donation_id: str,
    payload: DonationUpdate,
    donor_profile: ProfileResponse = Depends(require_donor),
    donation_service: DonationService = Depends(get_donation_service),
) -> DonationResponse:
    return await donation_service.update_donation(donation_id, donor_profile.id, payload)


@router.post(
    "/{donation_id}/post",
    response_model=DonationResponse,
    summary="Post Surplus Food Donation",
    description="Transitions draft donation to POSTED status so the rescue matching engine can discover eligible receivers.",
)
async def post_donation(
    donation_id: str,
    donor_profile: ProfileResponse = Depends(require_donor),
    donation_service: DonationService = Depends(get_donation_service),
) -> DonationResponse:
    return await donation_service.post_donation(donation_id, donor_profile.id)


@router.post(
    "/{donation_id}/cancel",
    response_model=DonationResponse,
    summary="Cancel Donation",
    description="Cancels an active or draft surplus donation.",
)
async def cancel_donation(
    donation_id: str,
    donor_profile: ProfileResponse = Depends(require_donor),
    donation_service: DonationService = Depends(get_donation_service),
) -> DonationResponse:
    return await donation_service.cancel_donation(donation_id, donor_profile.id)


@router.post(
    "/{donation_id}/ai-quality-check",
    response_model=FoodQualityAssessment,
    summary="Run AI-Powered Visual Food Quality Check",
    description="Analyzes donation food image using Google Gemini visual AI. Non-authoritative observational check only.",
)
async def check_donation_food_quality(
    donation_id: str,
    payload: Optional[FoodQualityCheckRequest] = None,
    current_profile: ProfileResponse = Depends(get_current_profile),
    ai_service: AIService = Depends(get_ai_service),
) -> FoodQualityAssessment:
    image_url = payload.image_url if payload else None
    raw_image_bytes = None
    mime_type = None
    if payload and payload.image_base64:
        import base64
        b64_str = payload.image_base64
        if "base64," in b64_str:
            header, b64_str = b64_str.split("base64,", 1)
            mime_type = header.replace("data:", "").replace(";", "")
        raw_image_bytes = base64.b64decode(b64_str)

    role_str = current_profile.role.value if hasattr(current_profile.role, "value") else str(current_profile.role)

    return await ai_service.analyze_donation_food_quality(
        donation_id=donation_id,
        user_id=current_profile.id,
        user_role=role_str,
        raw_image_bytes=raw_image_bytes,
        mime_type=mime_type,
        image_url=image_url,
    )
