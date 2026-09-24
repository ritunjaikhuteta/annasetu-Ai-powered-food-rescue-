"""Payment Provider and Webhook Schemas."""

from decimal import Decimal
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class PaymentOrderResponse(BaseModel):
    order_id: str
    amount: Decimal
    currency: str = "INR"
    provider: str
    status: str
    key_id: Optional[str] = None


class PaymentVerificationRequest(BaseModel):
    order_id: str
    payment_id: str
    signature: str


class PaymentRefundRequest(BaseModel):
    amount: Optional[Decimal] = Field(default=None, description="Partial refund amount, or None for full refund.")
    reason: str = Field(..., max_length=500, description="Auditable administrative refund reason.")


class PaymentRefundResponse(BaseModel):
    refund_id: str
    delivery_id: str
    refund_amount: Decimal
    wallet_id: str
    status: str
    message: str = "Refund successfully credited to NGO wallet."
