"""Handoff Verification Schemas."""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class HandoffType(str, Enum):
    PICKUP = "PICKUP"
    DELIVERY = "DELIVERY"


class HandoffStatus(str, Enum):
    PENDING = "PENDING"
    VERIFIED = "VERIFIED"
    EXPIRED = "EXPIRED"
    FAILED = "FAILED"
    MANUAL_REVIEW = "MANUAL_REVIEW"


class OTPGenerationResponse(BaseModel):
    delivery_id: str
    stop_id: Optional[str] = None
    handoff_type: HandoffType
    otp: str
    expires_at: str
    message: str = "Verification code issued. Share with the delivery partner upon arrival."


class HandoffVerificationRequest(BaseModel):
    otp: str = Field(..., min_length=4, max_length=10, description="Single-use numeric handoff OTP.")
    latitude: float = Field(..., ge=-90.0, le=90.0, description="Driver current latitude.")
    longitude: float = Field(..., ge=-180.0, le=180.0, description="Driver current longitude.")
    accuracy_meters: Optional[float] = Field(default=None, ge=0.0)


class HandoffVerificationResponse(BaseModel):
    id: str
    delivery_id: str
    stop_id: Optional[str] = None
    handoff_type: HandoffType
    status: HandoffStatus
    verified_by: Optional[str] = None
    verified_at: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    created_at: Optional[str] = None
