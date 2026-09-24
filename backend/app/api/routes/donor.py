"""Donor domain routes."""

from fastapi import APIRouter, Depends
from app.api.deps import get_donor_service, require_donor
from app.schemas.auth import ProfileResponse
from app.schemas.donor import DonorProfileResponse, DonorProfileUpdate
from app.services.donor_service import DonorService

router = APIRouter(prefix="/donor", tags=["Donor"])


@router.get(
    "/profile",
    response_model=DonorProfileResponse,
    summary="Get Donor Organization Profile",
    description="Retrieves donor business details, compliance numbers (FSSAI, GSTIN), and verification status. Enforces role = DONOR.",
)
async def get_donor_profile(
    donor_profile: ProfileResponse = Depends(require_donor),
    donor_service: DonorService = Depends(get_donor_service),
) -> DonorProfileResponse:
    return await donor_service.get_donor_profile(donor_profile.id)


@router.patch(
    "/profile",
    response_model=DonorProfileResponse,
    summary="Update Donor Organization Profile",
    description="Updates editable donor details. Protected fields (verification_status, subscription_plan) cannot be altered by the client.",
)
async def update_donor_profile(
    payload: DonorProfileUpdate,
    donor_profile: ProfileResponse = Depends(require_donor),
    donor_service: DonorService = Depends(get_donor_service),
) -> DonorProfileResponse:
    return await donor_service.update_donor_profile(donor_profile.id, payload)
