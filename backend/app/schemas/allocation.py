"""Pydantic schemas for Donation Allocations."""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class AllocationStatus(str, Enum):
    RESERVED = "RESERVED"
    ACCEPTED = "ACCEPTED"
    RELEASED = "RELEASED"
    FULFILLED = "FULFILLED"
    CANCELLED = "CANCELLED"


class AllocationCreate(BaseModel):
    donation_id: str = Field(..., description="Donation UUID to allocate from")
    need_id: str = Field(..., description="Target NGO Need UUID")
    match_id: Optional[str] = Field(None, description="Optional associated match UUID")
    allocated_quantity_kg: float = Field(..., gt=0, description="Quantity in kg to allocate")


class AllocationResponse(BaseModel):
    id: str
    donation_id: str
    need_id: str
    match_id: Optional[str] = None
    allocated_quantity_kg: float
    status: AllocationStatus
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
