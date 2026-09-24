"""Delivery Offer Schemas."""

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class DeliveryOfferStatus(str, Enum):
    OFFERED = "OFFERED"
    VIEWED = "VIEWED"
    ACCEPTED = "ACCEPTED"
    DECLINED = "DECLINED"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"


class DeliveryOfferCreate(BaseModel):
    driver_ids: Optional[List[str]] = Field(None, description="Specific driver IDs to offer, or empty for automatic dispatch to eligible drivers")


class DeliveryOfferResponse(BaseModel):
    id: str
    delivery_id: str
    driver_id: str
    vehicle_type: str
    offered_delivery_charge: float
    estimated_driver_payout: float
    estimated_distance_km: float
    estimated_duration_minutes: int
    expires_at: str
    status: DeliveryOfferStatus
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
