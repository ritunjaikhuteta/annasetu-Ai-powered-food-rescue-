"""Donation Allocation Routes."""

from fastapi import APIRouter, Depends, status
from app.api.deps import get_allocation_service, require_role
from app.schemas.allocation import AllocationCreate, AllocationResponse
from app.schemas.auth import ProfileResponse
from app.schemas.common import UserRole
from app.services.allocation_service import AllocationService

router = APIRouter(prefix="/allocations", tags=["Allocations"])


@router.post(
    "",
    response_model=AllocationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Allocate Donation to Need",
    description="Atomically commits a portion of a donation to an active NGO need. Enforces CAS optimistic locking to guarantee race condition and over-allocation prevention. Enforces role = DONOR or RECEIVER or ADMIN.",
)
async def create_allocation(
    payload: AllocationCreate,
    current_profile: ProfileResponse = Depends(require_role(UserRole.DONOR, UserRole.RECEIVER, UserRole.ADMIN)),
    allocation_service: AllocationService = Depends(get_allocation_service),
) -> AllocationResponse:
    return await allocation_service.create_allocation(
        payload=payload,
        user_id=current_profile.id,
        user_role=current_profile.role.value,
    )
