"""Delivery and Multi-Stop Route Schemas."""

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class DeliveryStatus(str, Enum):
    OPEN = "OPEN"
    ACCEPTED = "ACCEPTED"
    ARRIVING_PICKUP = "ARRIVING_PICKUP"
    PICKED_UP = "PICKED_UP"
    IN_TRANSIT = "IN_TRANSIT"
    AT_STOP = "AT_STOP"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"
    FAILED_PICKUP = "FAILED_PICKUP"
    FAILED_DELIVERY = "FAILED_DELIVERY"
    REASSIGNMENT_REQUIRED = "REASSIGNMENT_REQUIRED"


class DeliveryStopType(str, Enum):
    PICKUP = "PICKUP"
    DELIVERY = "DELIVERY"


class DeliveryStopStatus(str, Enum):
    PENDING = "PENDING"
    ARRIVING = "ARRIVING"
    ARRIVED = "ARRIVED"
    VERIFIED = "VERIFIED"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


class DeliveryCreate(BaseModel):
    donation_id: str = Field(..., description="Donation UUID")
    allocation_ids: List[str] = Field(..., min_length=1, max_length=3, description="List of 1 to 3 allocated batch UUIDs")


class DeliveryStopResponse(BaseModel):
    id: str
    delivery_id: str
    sequence_number: int
    stop_type: DeliveryStopType
    location_id: str
    receiver_id: Optional[str] = None
    allocation_id: Optional[str] = None
    quantity_kg: float
    distance_from_prev_km: float
    estimated_arrival: str
    status: DeliveryStopStatus
    arrived_at: Optional[str] = None
    completed_at: Optional[str] = None


class DeliveryResponse(BaseModel):
    id: str
    donation_id: str
    driver_id: Optional[str] = None
    vehicle_type: Optional[str] = None
    total_quantity_kg: float
    total_distance_km: float
    estimated_duration_minutes: int
    status: DeliveryStatus
    accepted_at: Optional[str] = None
    picked_up_at: Optional[str] = None
    completed_at: Optional[str] = None
    stops: List[DeliveryStopResponse] = Field(default_factory=list)
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class ProximityCheckRequest(BaseModel):
    latitude: Optional[float] = Field(None, ge=-90.0, le=90.0, description="Driver current latitude")
    longitude: Optional[float] = Field(None, ge=-180.0, le=180.0, description="Driver current longitude")
