"""Food Rescue Matching Routes."""

from typing import List
from fastapi import APIRouter, Depends
from app.api.deps import get_matching_service, require_donor, require_receiver
from app.schemas.auth import ProfileResponse
from app.schemas.match import MatchResponse
from app.services.matching_service import MatchingService

router = APIRouter(tags=["Matching"])


@router.post(
    "/donations/{donation_id}/generate-matches",
    response_model=List[MatchResponse],
    summary="Generate Deterministic Matches for Donation",
    description="Evaluates all hard eligibility constraints and calculates deterministic rescue priority scores for eligible receiver needs. Enforces role = DONOR.",
)
async def generate_matches_for_donation(
    donation_id: str,
    donor_profile: ProfileResponse = Depends(require_donor),
    matching_service: MatchingService = Depends(get_matching_service),
) -> List[MatchResponse]:
    return await matching_service.generate_matches_for_donation(donation_id, donor_id=donor_profile.id)


@router.get(
    "/donations/{donation_id}/matches",
    response_model=List[MatchResponse],
    summary="Get Matches for Donation",
    description="Returns persisted matches for a donation ordered by rescue priority. Enforces role = DONOR.",
)
async def get_matches_for_donation(
    donation_id: str,
    donor_profile: ProfileResponse = Depends(require_donor),
    matching_service: MatchingService = Depends(get_matching_service),
) -> List[MatchResponse]:
    return await matching_service.get_matches_for_donation(donation_id, donor_id=donor_profile.id)


@router.get(
    "/needs/{need_id}/matches",
    response_model=List[MatchResponse],
    summary="Get Matches for Need",
    description="Returns incoming matches for an NGO need ordered by rescue priority. Enforces role = RECEIVER.",
)
async def get_matches_for_need(
    need_id: str,
    receiver_profile: ProfileResponse = Depends(require_receiver),
    matching_service: MatchingService = Depends(get_matching_service),
) -> List[MatchResponse]:
    return await matching_service.get_matches_for_need(need_id, receiver_id=receiver_profile.id)
