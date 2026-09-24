"""Admin Operations Routes: Active Rescues, Exceptions, Reassignment, and Inspection."""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, Query
from app.api.deps import get_admin_operations_service, require_admin
from app.schemas.admin import PaginatedResponse
from app.schemas.admin_operations import (
    ActiveRescueDelivery,
    DeliveryExceptionItem,
    ReassignDeliveryRequest,
)
from app.schemas.auth import ProfileResponse
from app.services.admin_operations_service import AdminOperationsService

router = APIRouter(prefix="/admin", tags=["Admin Operations"])


@router.get(
    "/operations/active",
    response_model=List[ActiveRescueDelivery],
    summary="List Active Rescue Missions",
    description="Retrieves live ongoing rescue deliveries, stops progress, driver assignments, and urgency levels.",
)
async def list_active_operations(
    current_admin: ProfileResponse = Depends(require_admin),
    service: AdminOperationsService = Depends(get_admin_operations_service),
) -> List[ActiveRescueDelivery]:
    return await service.list_active_operations()


@router.get(
    "/operations/exceptions",
    response_model=List[DeliveryExceptionItem],
    summary="List Delivery Exception Queue",
    description="Retrieves failed, cancelled, reassignment-required, and at-risk delivery missions.",
)
async def list_delivery_exceptions(
    current_admin: ProfileResponse = Depends(require_admin),
    service: AdminOperationsService = Depends(get_admin_operations_service),
) -> List[DeliveryExceptionItem]:
    return await service.list_delivery_exceptions()


@router.post(
    "/deliveries/{delivery_id}/reassign",
    response_model=Dict[str, Any],
    summary="Reassign Delivery to New Driver",
    description="Reassigns an at-risk or failed delivery to an available verified delivery partner.",
)
async def reassign_delivery(
    delivery_id: str,
    payload: ReassignDeliveryRequest,
    current_admin: ProfileResponse = Depends(require_admin),
    service: AdminOperationsService = Depends(get_admin_operations_service),
) -> Dict[str, Any]:
    return await service.reassign_delivery(
        delivery_id=delivery_id,
        admin_id=current_admin.id,
        payload=payload,
    )


# ---------------------------------------------------------------------------
# Inspection Endpoints: Donations, Needs, Matches, Allocations
# ---------------------------------------------------------------------------

@router.get(
    "/donations",
    response_model=PaginatedResponse[Dict[str, Any]],
    summary="Inspect Donations",
    description="Administrative listing of donations across all statuses.",
)
async def list_donations(
    status: Optional[str] = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_admin: ProfileResponse = Depends(require_admin),
    service: AdminOperationsService = Depends(get_admin_operations_service),
) -> PaginatedResponse[Dict[str, Any]]:
    return await service.list_donations(status=status, page=page, page_size=page_size)


@router.get(
    "/needs",
    response_model=PaginatedResponse[Dict[str, Any]],
    summary="Inspect Hunger Relief Needs",
    description="Administrative listing of NGO needs across all statuses.",
)
async def list_needs(
    status: Optional[str] = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_admin: ProfileResponse = Depends(require_admin),
    service: AdminOperationsService = Depends(get_admin_operations_service),
) -> PaginatedResponse[Dict[str, Any]]:
    return await service.list_needs(status=status, page=page, page_size=page_size)


@router.get(
    "/matches",
    response_model=PaginatedResponse[Dict[str, Any]],
    summary="Inspect Rescue Matches",
    description="Administrative inspection of deterministic matching results and priority scores.",
)
async def list_matches(
    donation_id: Optional[str] = Query(default=None),
    need_id: Optional[str] = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_admin: ProfileResponse = Depends(require_admin),
    service: AdminOperationsService = Depends(get_admin_operations_service),
) -> PaginatedResponse[Dict[str, Any]]:
    return await service.list_matches(donation_id=donation_id, need_id=need_id, page=page, page_size=page_size)


@router.get(
    "/allocations",
    response_model=PaginatedResponse[Dict[str, Any]],
    summary="Inspect Donation Allocations",
    description="Administrative inspection of split allocations and commitments.",
)
async def list_allocations(
    donation_id: Optional[str] = Query(default=None),
    receiver_id: Optional[str] = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_admin: ProfileResponse = Depends(require_admin),
    service: AdminOperationsService = Depends(get_admin_operations_service),
) -> PaginatedResponse[Dict[str, Any]]:
    return await service.list_allocations(donation_id=donation_id, receiver_id=receiver_id, page=page, page_size=page_size)
