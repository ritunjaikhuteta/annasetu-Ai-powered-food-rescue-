"""Wallet and Financial Transaction Schemas."""

from decimal import Decimal
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class TransactionType(str, Enum):
    TOP_UP = "TOP_UP"
    DELIVERY_CHARGE = "DELIVERY_CHARGE"
    PLATFORM_FEE = "PLATFORM_FEE"
    DRIVER_PAYOUT = "DRIVER_PAYOUT"
    RESERVATION = "RESERVATION"
    RESERVATION_RELEASE = "RESERVATION_RELEASE"
    REFUND = "REFUND"
    BONUS = "BONUS"
    ADJUSTMENT = "ADJUSTMENT"


class TransactionStatus(str, Enum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    REVERSED = "REVERSED"


class WalletResponse(BaseModel):
    id: str
    user_id: str
    owner_type: str = "RECEIVER"
    balance: Decimal = Field(..., description="Total committed wallet balance.")
    reserved_balance: Decimal = Field(default=Decimal("0.00"), description="Amount held for ongoing delivery missions.")
    available_balance: Decimal = Field(..., description="Available unencumbered balance (balance - reserved_balance).")
    currency: str = "INR"
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class TransactionResponse(BaseModel):
    id: str
    wallet_id: str
    user_id: str
    type: TransactionType
    amount: Decimal
    currency: str = "INR"
    status: TransactionStatus
    reference_id: Optional[str] = None
    reference_type: Optional[str] = None
    description: str
    created_at: Optional[str] = None


class WalletTopUpRequest(BaseModel):
    amount: Decimal = Field(..., gt=0, le=50000, description="Amount in INR to credit to wallet.")
    idempotency_key: Optional[str] = Field(default=None, description="Client-supplied idempotency key.")


class WalletTopUpResponse(BaseModel):
    wallet_id: str
    amount: Decimal
    new_balance: Decimal
    transaction_id: str
    status: str
    payment_reference: Optional[str] = None
    message: str = "Wallet top-up processed successfully."


class WalletReservationResponse(BaseModel):
    id: str
    wallet_id: str
    delivery_id: str
    reserved_amount: Decimal
    status: str
    created_at: Optional[str] = None
