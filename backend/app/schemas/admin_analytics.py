"""Admin Analytics Schemas."""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel


class TimePeriod(str, Enum):
    TODAY = "today"
    SEVEN_DAYS = "7d"
    THIRTY_DAYS = "30d"
    NINETY_DAYS = "90d"
    CUSTOM = "custom"


class ImpactAnalyticsResponse(BaseModel):
    period: str
    total_food_rescued_kg: float
    meal_equivalents: int
    co2e_avoided_kg: float
    active_donor_count: int
    active_receiver_count: int
    trends: List[Dict[str, Any]] = []


class OperationsAnalyticsResponse(BaseModel):
    period: str
    donations_posted: int
    donations_delivered: int
    delivery_completion_rate: float
    failure_rate: float
    average_delivery_time_minutes: float
    reassignment_count: int
    average_rescue_lead_time_hours: float


class FinancialAnalyticsResponse(BaseModel):
    period: str
    delivery_charges_total: float
    platform_fees_total: float
    driver_payouts_total: float
    refunds_total: float
    subscription_revenue_total: float
