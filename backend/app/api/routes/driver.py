"""Driver (Delivery Partner) domain routes."""

from fastapi import APIRouter, Depends
from app.api.deps import get_driver_service, require_driver
from app.schemas.auth import ProfileResponse
from app.schemas.driver import DriverProfileResponse, DriverProfileUpdate
from app.services.driver_service import DriverService

router = APIRouter(prefix="/driver", tags=["Driver"])


@router.get(
    "/profile",
    response_model=DriverProfileResponse,
    summary="Get Driver Partner Profile",
    description="Retrieves delivery partner vehicle details, online availability, and verification status. Enforces role = DRIVER.",
)
async def get_driver_profile(
    driver_profile: ProfileResponse = Depends(require_driver),
    driver_service: DriverService = Depends(get_driver_service),
) -> DriverProfileResponse:
    return await driver_service.get_driver_profile(driver_profile.id)


@router.patch(
    "/profile",
    response_model=DriverProfileResponse,
    summary="Update Driver Partner Profile",
    description="Updates vehicle type, license plate, refrigeration capability, online status, and location. Verification status cannot be altered.",
)
async def update_driver_profile(
    payload: DriverProfileUpdate,
    driver_profile: ProfileResponse = Depends(require_driver),
    driver_service: DriverService = Depends(get_driver_service),
) -> DriverProfileResponse:
    return await driver_service.update_driver_profile(driver_profile.id, payload)
