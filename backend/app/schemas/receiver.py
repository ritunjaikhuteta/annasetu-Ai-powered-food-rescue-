"""Receiver profile schemas."""

from typing import Any, Dict, Optional
from pydantic import BaseModel, Field
from app.schemas.common import VerificationStatus


class ReceiverProfileResponse(BaseModel):
    """Full receiver (NGO) profile response model."""

    id: str
    user_id: str
    organization_name: str
    organization_type: Optional[str] = None
    registration_number: Optional[str] = None
    darpan_id: Optional[str] = None
    pan_number: Optional[str] = None
    contact_person_name: Optional[str] = None
    beneficiary_count: Optional[int] = None
    storage_capacity_liters: Optional[float] = None
    has_refrigeration: bool = False
    operating_hours: Optional[Dict[str, Any]] = None
    verification_status: VerificationStatus = VerificationStatus.PENDING
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class ReceiverProfileUpdate(BaseModel):
    """Client update payload for receiver profile.
    Notice: verification_status is excluded to prevent client tampering.
    """

    organization_name: Optional[str] = Field(None, min_length=2, max_length=200)
    organization_type: Optional[str] = Field(None, max_length=100)
    registration_number: Optional[str] = Field(None, max_length=100)
    darpan_id: Optional[str] = Field(None, max_length=100)
    pan_number: Optional[str] = Field(None, max_length=20)
    contact_person_name: Optional[str] = Field(None, max_length=150)
    beneficiary_count: Optional[int] = Field(None, ge=0)
    storage_capacity_liters: Optional[float] = Field(None, ge=0)
    has_refrigeration: Optional[bool] = None
    operating_hours: Optional[Dict[str, Any]] = None
