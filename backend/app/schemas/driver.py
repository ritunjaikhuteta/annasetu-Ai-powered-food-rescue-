"""Driver (Delivery Partner) Schemas."""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field
from app.schemas.common import VerificationStatus


class DriverAvailabilityStatus(str, Enum):
    AVAILABLE = "AVAILABLE"
    ON_JOB = "ON_JOB"
    OFFLINE = "OFFLINE"


class DriverProfileResponse(BaseModel):
    """Full driver / delivery partner profile response model."""

    id: str
    user_id: str
    driving_license_number: Optional[str] = None
    vehicle_type: Optional[str] = None
    vehicle_number: Optional[str] = None
    vehicle_capacity_kg: Optional[float] = None
    has_refrigeration: bool = False
    is_online: bool = False
    availability_status: DriverAvailabilityStatus = DriverAvailabilityStatus.AVAILABLE
    current_latitude: Optional[float] = None
    current_longitude: Optional[float] = None
    verification_status: VerificationStatus = VerificationStatus.PENDING
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class DriverProfileUpdate(BaseModel):
    """Client update payload for driver profile.
    Notice: verification_status is excluded to prevent client tampering.
    """

    vehicle_type: Optional[str] = Field(None, max_length=50)
    vehicle_number: Optional[str] = Field(None, max_length=50)
    vehicle_capacity_kg: Optional[float] = Field(None, ge=0)
    has_refrigeration: Optional[bool] = None
    is_online: Optional[bool] = None
    availability_status: Optional[DriverAvailabilityStatus] = None
    current_latitude: Optional[float] = Field(None, ge=-90.0, le=90.0)
    current_longitude: Optional[float] = Field(None, ge=-180.0, le=180.0)


class DriverLocationUpdate(BaseModel):
    """Payload for driver GPS telemetry update."""

    latitude: float = Field(..., ge=-90.0, le=90.0, description="Latitude coordinate")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="Longitude coordinate")
    accuracy_meters: Optional[float] = Field(None, ge=0.0, le=1000.0, description="GPS accuracy in meters")


class DriverLocationResponse(BaseModel):
    id: str
    driver_id: str
    latitude: float
    longitude: float
    accuracy_meters: Optional[float] = None
    recorded_at: str


class EligibleDriverResponse(BaseModel):
    """Suggested eligible driver for dispatch matching."""

    id: str
    driver_user_id: str
    name: str
    phone: Optional[str] = None
    vehicle_type: str
    vehicle_number: Optional[str] = None
    vehicle_capacity_kg: float
    has_refrigeration: bool
    distance_to_pickup_km: float
    pickup_eta_minutes: int
    availability_status: DriverAvailabilityStatus
    verification_status: VerificationStatus
