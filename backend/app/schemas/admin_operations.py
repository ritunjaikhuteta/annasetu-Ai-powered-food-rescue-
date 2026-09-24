"""Admin Operations & Delivery Exceptions Schemas."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ActiveRescueDelivery(BaseModel):
    delivery_id: str
    status: str
    driver_id: Optional[str] = None
    driver_name: Optional[str] = None
    vehicle_type: Optional[str] = None
    donation_id: str
    food_name: Optional[str] = None
    quantity_kg: float
    pickup_location_ref: str
    delivery_stops_count: int
    current_stop: Optional[str] = None
    estimated_eta: Optional[str] = None
    deadline: Optional[str] = None
    route_status: str
    handoff_status: str
    integrity_status: str
    urgency_level: str = "NORMAL"  # NORMAL, ELEVATED, AT_RISK


class DeliveryExceptionItem(BaseModel):
    delivery_id: str
    status: str
    exception_type: str  # FAILED_PICKUP, FAILED_DELIVERY, REASSIGNMENT_REQUIRED, CANCELLED, AT_RISK
    urgency: str  # CRITICAL, HIGH, MEDIUM
    reason: str
    driver_id: Optional[str] = None
    created_at: str
    deadline: Optional[str] = None


class ReassignDeliveryRequest(BaseModel):
    new_driver_id: str = Field(..., min_length=1)
    reason: str = Field(..., min_length=3, max_length=500)


class AdminUserItem(BaseModel):
    id: str
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    role: str
    is_active: bool
    verification_status: Optional[str] = None
    created_at: Optional[str] = None
    business_or_org_name: Optional[str] = None


class UserActionRequest(BaseModel):
    reason: str = Field(..., min_length=3, max_length=500)
