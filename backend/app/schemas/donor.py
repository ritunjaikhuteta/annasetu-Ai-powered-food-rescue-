"""Donor profile schemas."""

from typing import Any, Dict, Optional
from pydantic import BaseModel, Field
from app.schemas.common import VerificationStatus


class DonorProfileResponse(BaseModel):
    """Full donor profile response model."""

    id: str
    user_id: str
    business_name: str
    business_type: Optional[str] = None
    fssai_license_number: Optional[str] = None
    gstin: Optional[str] = None
    contact_person_name: Optional[str] = None
    pickup_instructions: Optional[str] = None
    operating_hours: Optional[Dict[str, Any]] = None
    verification_status: VerificationStatus = VerificationStatus.PENDING
    subscription_plan: Optional[str] = "FREE"
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class DonorProfileUpdate(BaseModel):
    """Client update payload for donor profile.
    Notice: verification_status and subscription_plan are excluded to prevent client tampering.
    """

    business_name: Optional[str] = Field(None, min_length=2, max_length=200)
    business_type: Optional[str] = Field(None, max_length=100)
    fssai_license_number: Optional[str] = Field(None, max_length=50)
    gstin: Optional[str] = Field(None, max_length=50)
    contact_person_name: Optional[str] = Field(None, max_length=150)
    pickup_instructions: Optional[str] = Field(None, max_length=1000)
    operating_hours: Optional[Dict[str, Any]] = None
