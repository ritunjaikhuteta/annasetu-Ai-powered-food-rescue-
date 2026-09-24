"""Donor Surplus Food Donation Routes."""

from typing import List, Optional
from fastapi import APIRouter, Depends, status
from app.api.deps import get_donation_service, require_donor
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
