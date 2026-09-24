"""Pydantic schemas for Matches and Explainable Priority Breakdown."""

from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class MatchStatus(str, Enum):
    PROPOSED = "PROPOSED"
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


class PriorityLabel(str, Enum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class PriorityBreakdown(BaseModel):
    distance_km: float
    estimated_travel_minutes: int
    expiry_buffer_minutes: int
    fulfillment_percent: float
    capacity_available_kg: float
    route_feasible: bool
    expiry_score: float
    eta_score: float
    distance_score: float
    fulfillment_score: float
    route_score: float
    priority_score: float


class MatchResponse(BaseModel):
    id: str
    donation_id: str
    need_id: str
    priority_score: float
    priority_label: PriorityLabel
    distance_km: float
    estimated_travel_minutes: int
    estimated_arrival_at: str
    expiry_buffer_minutes: int
    fulfillable_quantity_kg: float
    fulfillment_percent: float
    priority_breakdown: Dict[str, Any]
    explanation: str
    status: MatchStatus
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
