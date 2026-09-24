"""Receiver (NGO) domain routes."""

from fastapi import APIRouter, Depends
from app.api.deps import get_receiver_service, require_receiver
from app.schemas.auth import ProfileResponse
from app.schemas.receiver import ReceiverProfileResponse, ReceiverProfileUpdate
from app.services.receiver_service import ReceiverService

router = APIRouter(prefix="/receiver", tags=["Receiver"])


@router.get(
    "/profile",
    response_model=ReceiverProfileResponse,
    summary="Get Receiver NGO Profile",
    description="Retrieves NGO details, registration numbers, Darpan ID, and verification status. Enforces role = RECEIVER.",
)
async def get_receiver_profile(
    receiver_profile: ProfileResponse = Depends(require_receiver),
    receiver_service: ReceiverService = Depends(get_receiver_service),
) -> ReceiverProfileResponse:
    return await receiver_service.get_receiver_profile(receiver_profile.id)


@router.patch(
    "/profile",
    response_model=ReceiverProfileResponse,
    summary="Update Receiver NGO Profile",
    description="Updates editable receiver fields. Verification status cannot be changed by the client.",
)
async def update_receiver_profile(
    payload: ReceiverProfileUpdate,
    receiver_profile: ProfileResponse = Depends(require_receiver),
    receiver_service: ReceiverService = Depends(get_receiver_service),
) -> ReceiverProfileResponse:
    return await receiver_service.update_receiver_profile(receiver_profile.id, payload)
