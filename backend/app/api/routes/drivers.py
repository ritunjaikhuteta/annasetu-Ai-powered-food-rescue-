"""Driver Operations API Routes."""

from typing import List
from fastapi import APIRouter, Depends, status
from app.api.deps import (
    get_delivery_service,
    get_driver_service,
    require_driver,
)
from app.schemas.auth import ProfileResponse
from app.schemas.delivery import DeliveryResponse
from app.schemas.driver import (
    DriverLocationResponse,
    DriverLocationUpdate,
)
from app.services.delivery_service import DeliveryService
from app.services.driver_service import DriverService

router = APIRouter(prefix="/driver", tags=["Driver"])


@router.get(
    "/deliveries",
    response_model=List[DeliveryResponse],
    summary="Get Assigned Driver Deliveries",
    description="Retrieves active and completed rescue delivery missions assigned to the authenticated driver partner.",
)
async def get_my_deliveries(
    driver_profile: ProfileResponse = Depends(require_driver),
    delivery_service: DeliveryService = Depends(get_delivery_service),
) -> List[DeliveryResponse]:
    return await delivery_service.get_driver_deliveries(driver_profile.id)


@router.get(
    "/deliveries/{delivery_id}",
    response_model=DeliveryResponse,
    summary="Get Driver Delivery Details",
    description="Retrieves details and stop sequences for a delivery assigned to the driver.",
)
async def get_driver_delivery(
    delivery_id: str,
    driver_profile: ProfileResponse = Depends(require_driver),
    delivery_service: DeliveryService = Depends(get_delivery_service),
) -> DeliveryResponse:
    delivery = await delivery_service.get_delivery(delivery_id)
    return delivery


@router.post(
    "/location",
    response_model=DriverLocationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Update Driver Location Telemetry",
    description="Records recent GPS coordinates for delivery partner discovery and dispatch proximity validation.",
)
async def update_location(
    payload: DriverLocationUpdate,
    driver_profile: ProfileResponse = Depends(require_driver),
    driver_service: DriverService = Depends(get_driver_service),
) -> DriverLocationResponse:
    return await driver_service.record_location(driver_profile.id, payload)
