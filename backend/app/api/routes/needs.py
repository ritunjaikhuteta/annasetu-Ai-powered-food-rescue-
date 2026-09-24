"""Receiver NGO Needs Routes."""

from typing import List, Optional
from fastapi import APIRouter, Depends, status
from app.api.deps import get_need_service, require_receiver
from app.schemas.auth import ProfileResponse
from app.schemas.need import NeedCreate, NeedResponse, NeedStatus, NeedUpdate
from app.services.need_service import NeedService

router = APIRouter(prefix="/needs", tags=["Needs"])


@router.post(
    "",
    response_model=NeedResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a New Food Need",
    description="Creates a new NGO food need in DRAFT state. Enforces role = RECEIVER.",
)
async def create_need(
    payload: NeedCreate,
    receiver_profile: ProfileResponse = Depends(require_receiver),
    need_service: NeedService = Depends(get_need_service),
) -> NeedResponse:
    return await need_service.create_need(receiver_profile.id, payload)


@router.get(
    "",
    response_model=List[NeedResponse],
    summary="List NGO Needs",
    description="Retrieves all food needs created by the authenticated receiver organization.",
)
async def list_needs(
    status_filter: Optional[NeedStatus] = None,
    receiver_profile: ProfileResponse = Depends(require_receiver),
    need_service: NeedService = Depends(get_need_service),
) -> List[NeedResponse]:
    return await need_service.list_needs(receiver_profile.id, status=status_filter)


@router.get(
    "/{need_id}",
    response_model=NeedResponse,
    summary="Get Need Details",
    description="Retrieves details of a specific need owned by the receiver.",
)
async def get_need(
    need_id: str,
    receiver_profile: ProfileResponse = Depends(require_receiver),
    need_service: NeedService = Depends(get_need_service),
) -> NeedResponse:
    return await need_service.get_need(need_id, receiver_id=receiver_profile.id)


@router.patch(
    "/{need_id}",
    response_model=NeedResponse,
    summary="Update Food Need",
    description="Updates editable need fields while in DRAFT or ACTIVE status.",
)
async def update_need(
    need_id: str,
    payload: NeedUpdate,
    receiver_profile: ProfileResponse = Depends(require_receiver),
    need_service: NeedService = Depends(get_need_service),
) -> NeedResponse:
    return await need_service.update_need(need_id, receiver_profile.id, payload)


@router.post(
    "/{need_id}/activate",
    response_model=NeedResponse,
    summary="Activate Food Need",
    description="Transitions draft need to ACTIVE status so it can be matched with surplus donations.",
)
async def activate_need(
    need_id: str,
    receiver_profile: ProfileResponse = Depends(require_receiver),
    need_service: NeedService = Depends(get_need_service),
) -> NeedResponse:
    return await need_service.activate_need(need_id, receiver_profile.id)


@router.post(
    "/{need_id}/cancel",
    response_model=NeedResponse,
    summary="Cancel Food Need",
    description="Cancels an active or draft need.",
)
async def cancel_need(
    need_id: str,
    receiver_profile: ProfileResponse = Depends(require_receiver),
    need_service: NeedService = Depends(get_need_service),
) -> NeedResponse:
    return await need_service.cancel_need(need_id, receiver_profile.id)
