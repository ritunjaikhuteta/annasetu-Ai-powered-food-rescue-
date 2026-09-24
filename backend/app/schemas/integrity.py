"""Food Integrity Check and Manual Review Schemas."""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class ManualReviewStatus(str, Enum):
    PENDING = "PENDING"
    CLEARED = "CLEARED"
    REQUIRES_ACTION = "REQUIRES_ACTION"
    DISPUTED = "DISPUTED"


class FoodIntegrityCheckResponse(BaseModel):
    id: str
    delivery_id: str
    stop_id: Optional[str] = None
    check_type: str = "PACKAGE_VISUAL_CONSISTENCY"
    pickup_image_path: Optional[str] = None
    delivery_image_path: Optional[str] = None
    seal_id: Optional[str] = None
    pickup_seal_status: Optional[str] = None
    delivery_seal_status: Optional[str] = None
    ai_integrity_score: Optional[float] = None
    tampering_signal: bool = False
    ai_reason: Optional[str] = None
    manual_review_status: ManualReviewStatus = ManualReviewStatus.PENDING
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class ManualReviewRequest(BaseModel):
    status: ManualReviewStatus = Field(..., description="Review outcome: CLEARED, REQUIRES_ACTION, or DISPUTED.")
    notes: Optional[str] = Field(default=None, max_length=1000, description="Auditable reviewer explanation.")
