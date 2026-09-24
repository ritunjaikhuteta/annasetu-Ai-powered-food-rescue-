"""Donor Subscription Schemas."""

from decimal import Decimal
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class BillingCycle(str, Enum):
    MONTHLY = "MONTHLY"
    YEARLY = "YEARLY"


class SubscriptionStatus(str, Enum):
    TRIAL = "TRIAL"
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"


class SubscriptionPlanResponse(BaseModel):
    id: str
    name: str
    code: str
    monthly_price: Decimal
    yearly_price: Decimal
    currency: str = "INR"
    features: Dict[str, Any]
    is_active: bool = True


class SubscriptionCheckoutRequest(BaseModel):
    plan_id: str = Field(..., description="ID of the subscription plan to purchase.")
    billing_cycle: BillingCycle = Field(default=BillingCycle.MONTHLY, description="MONTHLY or YEARLY.")


class SubscriptionResponse(BaseModel):
    id: str
    user_id: str
    plan_id: str
    plan_name: str
    billing_cycle: BillingCycle
    amount: Decimal
    status: SubscriptionStatus
    current_period_start: str
    current_period_end: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
