"""Admin Financial Exceptions and Adjustments Schemas."""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class FinancialExceptionType(str, Enum):
    UNSETTLED_RESERVATION = "UNSETTLED_RESERVATION"
    SETTLEMENT_FAILED = "SETTLEMENT_FAILED"
    PAYOUT_FAILED = "PAYOUT_FAILED"
    REFUND_FAILED = "REFUND_FAILED"
    PAYMENT_MISMATCH = "PAYMENT_MISMATCH"
    BALANCE_INVARIANT_VIOLATION = "BALANCE_INVARIANT_VIOLATION"


class FinancialExceptionItem(BaseModel):
    id: str
    exception_type: str
    severity: str  # HIGH, MEDIUM, LOW
    related_entity_id: str
    description: str
    amount: Optional[float] = None
    created_at: str


class FinancialReviewRequest(BaseModel):
    notes: str = Field(..., min_length=3, max_length=500)
    status: str = "RESOLVED"


class FinancialAdjustRequest(BaseModel):
    wallet_id: str
    amount: float = Field(..., gt=0.0)
    adjustment_type: str = Field(..., pattern="^(CREDIT|DEBIT)$")
    reason: str = Field(..., min_length=3, max_length=500)
    original_reference_id: Optional[str] = None
