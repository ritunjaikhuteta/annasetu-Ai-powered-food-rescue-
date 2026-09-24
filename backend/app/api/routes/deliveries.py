"""Delivery and Logistics API Routes."""

from typing import List, Optional
from fastapi import APIRouter, Depends, status
from app.api.deps import (
    get_delivery_service,
    get_driver_service,
    require_driver,
    require_role,
)
from app.schemas.auth import ProfileResponse
from app.schemas.common import UserRole
from app.schemas.delivery import (
    DeliveryCreate,
    DeliveryResponse,
    DeliveryStatus,
    ProximityCheckRequest,
)
from app.schemas.delivery_offer import (
    DeliveryOfferCreate,
    DeliveryOfferResponse,
)
from app.schemas.driver import EligibleDriverResponse
from app.services.delivery_service import DeliveryService

router = APIRouter(tags=["Deliveries"])


@router.post(
    "/deliveries",
    response_model=DeliveryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Delivery Mission",
    description="Creates a multi-stop rescue delivery from accepted allocations, evaluating route feasibility deterministically.",
)
async def create_delivery(
    payload: DeliveryCreate,
    current_profile: ProfileResponse = Depends(require_role(UserRole.DONOR, UserRole.ADMIN, UserRole.RECEIVER)),
    delivery_service: DeliveryService = Depends(get_delivery_service),
) -> DeliveryResponse:
    return await delivery_service.create_delivery(
        payload=payload,
        creator_id=current_profile.id,
        creator_role=current_profile.role.value,
    )


@router.get(
    "/deliveries/{delivery_id}",
    response_model=DeliveryResponse,
    summary="Get Delivery Mission Details",
    description="Retrieves delivery mission details with sequenced stops and status.",
)
async def get_delivery(
    delivery_id: str,
    current_profile: ProfileResponse = Depends(require_role(UserRole.DONOR, UserRole.RECEIVER, UserRole.DRIVER, UserRole.ADMIN)),
    delivery_service: DeliveryService = Depends(get_delivery_service),
) -> DeliveryResponse:
    return await delivery_service.get_delivery(delivery_id)


@router.get(
    "/deliveries/{delivery_id}/eligible-drivers",
    response_model=List[EligibleDriverResponse],
    summary="Discover Eligible Drivers",
    description="Discovers and deterministically ranks verified, available delivery partners with sufficient vehicle capacity.",
)
async def get_eligible_drivers(
    delivery_id: str,
    current_profile: ProfileResponse = Depends(require_role(UserRole.DONOR, UserRole.ADMIN)),
    delivery_service: DeliveryService = Depends(get_delivery_service),
) -> List[EligibleDriverResponse]:
    return await delivery_service.get_eligible_drivers(delivery_id)


@router.post(
    "/deliveries/{delivery_id}/offers",
    response_model=List[DeliveryOfferResponse],
    summary="Dispatch Delivery Offers",
    description="Dispatches delivery mission offers to eligible drivers.",
)
async def create_delivery_offers(
    delivery_id: str,
    payload: Optional[DeliveryOfferCreate] = None,
    current_profile: ProfileResponse = Depends(require_role(UserRole.DONOR, UserRole.ADMIN)),
    delivery_service: DeliveryService = Depends(get_delivery_service),
) -> List[DeliveryOfferResponse]:
    driver_ids = payload.driver_ids if payload else None
    return await delivery_service.create_offers(delivery_id, driver_ids=driver_ids)


@router.post(
    "/delivery-offers/{offer_id}/view",
    response_model=DeliveryOfferResponse,
    summary="Mark Offer Viewed",
    description="Marks a dispatched offer as viewed by the recipient driver.",
)
async def view_offer(
    offer_id: str,
    driver_profile: ProfileResponse = Depends(require_driver),
    delivery_service: DeliveryService = Depends(get_delivery_service),
) -> DeliveryOfferResponse:
    return await delivery_service.view_offer(offer_id, driver_profile.id)


@router.post(
    "/delivery-offers/{offer_id}/accept",
    response_model=DeliveryResponse,
    summary="Accept Delivery Offer",
    description="Atomically commits offer acceptance. Uses CAS locking so exactly one driver partner wins the assignment.",
)
async def accept_offer(
    offer_id: str,
    driver_profile: ProfileResponse = Depends(require_driver),
    delivery_service: DeliveryService = Depends(get_delivery_service),
) -> DeliveryResponse:
    return await delivery_service.accept_offer(offer_id, driver_profile.id)


@router.post(
    "/delivery-offers/{offer_id}/decline",
    response_model=DeliveryOfferResponse,
    summary="Decline Delivery Offer",
    description="Declines a dispatched offer.",
)
async def decline_offer(
    offer_id: str,
    driver_profile: ProfileResponse = Depends(require_driver),
    delivery_service: DeliveryService = Depends(get_delivery_service),
) -> DeliveryOfferResponse:
    return await delivery_service.decline_offer(offer_id, driver_profile.id)


@router.post(
    "/deliveries/{delivery_id}/cancel",
    response_model=DeliveryResponse,
    summary="Cancel Delivery Mission",
    description="Cancels delivery or triggers reassignment if cancelled by driver.",
)
async def cancel_delivery(
    delivery_id: str,
    current_profile: ProfileResponse = Depends(require_role(UserRole.DONOR, UserRole.DRIVER, UserRole.ADMIN)),
    delivery_service: DeliveryService = Depends(get_delivery_service),
) -> DeliveryResponse:
    return await delivery_service.cancel_delivery(delivery_id, current_profile.id, current_profile.role.value)


@router.post(
    "/deliveries/{delivery_id}/arrive-pickup",
    response_model=DeliveryResponse,
    summary="Driver Arrived at Pickup",
    description="Updates delivery state to ARRIVING_PICKUP with GPS proximity verification.",
)
async def arrive_pickup(
    delivery_id: str,
    proximity: Optional[ProximityCheckRequest] = None,
    driver_profile: ProfileResponse = Depends(require_driver),
    delivery_service: DeliveryService = Depends(get_delivery_service),
) -> DeliveryResponse:
    return await delivery_service.update_delivery_status(
        delivery_id,
        DeliveryStatus.ARRIVING_PICKUP,
        driver_profile.id,
        proximity=proximity,
    )


@router.post(
    "/deliveries/{delivery_id}/mark-picked-up",
    response_model=DeliveryResponse,
    summary="Food Loaded and Picked Up",
    description="Transitions state to PICKED_UP and marks pickup stop COMPLETED.",
)
async def mark_picked_up(
    delivery_id: str,
    driver_profile: ProfileResponse = Depends(require_driver),
    delivery_service: DeliveryService = Depends(get_delivery_service),
) -> DeliveryResponse:
    return await delivery_service.update_delivery_status(
        delivery_id,
        DeliveryStatus.PICKED_UP,
        driver_profile.id,
    )


@router.post(
    "/deliveries/{delivery_id}/start-transit",
    response_model=DeliveryResponse,
    summary="Driver In Transit to Next Stop",
    description="Transitions state to IN_TRANSIT.",
)
async def start_transit(
    delivery_id: str,
    driver_profile: ProfileResponse = Depends(require_driver),
    delivery_service: DeliveryService = Depends(get_delivery_service),
) -> DeliveryResponse:
    return await delivery_service.update_delivery_status(
        delivery_id,
        DeliveryStatus.IN_TRANSIT,
        driver_profile.id,
    )


@router.post(
    "/deliveries/{delivery_id}/arrive-stop",
    response_model=DeliveryResponse,
    summary="Driver Arrived at Delivery Stop",
    description="Transitions state to AT_STOP with GPS proximity verification.",
)
async def arrive_stop(
    delivery_id: str,
    proximity: Optional[ProximityCheckRequest] = None,
    driver_profile: ProfileResponse = Depends(require_driver),
    delivery_service: DeliveryService = Depends(get_delivery_service),
) -> DeliveryResponse:
    return await delivery_service.update_delivery_status(
        delivery_id,
        DeliveryStatus.AT_STOP,
        driver_profile.id,
        proximity=proximity,
    )


@router.post(
    "/deliveries/{delivery_id}/complete-stop",
    response_model=DeliveryResponse,
    summary="Complete Delivery Stop",
    description="Completes delivery stop or finishes full mission (DELIVERED).",
)
async def complete_stop(
    delivery_id: str,
    driver_profile: ProfileResponse = Depends(require_driver),
    delivery_service: DeliveryService = Depends(get_delivery_service),
) -> DeliveryResponse:
    return await delivery_service.update_delivery_status(
        delivery_id,
        DeliveryStatus.DELIVERED,
        driver_profile.id,
    )
