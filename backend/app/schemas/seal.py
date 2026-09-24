"""Package Seal Schemas."""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class SealStatus(str, Enum):
    NOT_RECORDED = "NOT_RECORDED"
    INTACT = "INTACT"
    BROKEN = "BROKEN"
    MISSING = "MISSING"
    DISPUTED = "DISPUTED"


class PackageSealRecordRequest(BaseModel):
    seal_status: SealStatus = Field(..., description="Observed tamper-evident seal condition.")
    notes: Optional[str] = Field(default=None, max_length=500)


class PackageSealResponse(BaseModel):
    id: str
    donation_id: str
    delivery_id: str
    seal_id: str
    applied_by: Optional[str] = None
    applied_at: Optional[str] = None
    pickup_status: SealStatus = SealStatus.INTACT
    delivery_status: SealStatus = SealStatus.NOT_RECORDED
    verified_at: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
