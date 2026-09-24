"""Pricing and Financial Breakdown Schemas."""

from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field


class DeliveryPricingResponse(BaseModel):
    delivery_id: str
    base_fare: Decimal = Field(..., description="Base mobilization fare.")
    distance_km: float = Field(..., description="Calculated road travel distance in kilometers.")
    distance_charge: Decimal = Field(..., description="Distance component of delivery fee.")
    duration_minutes: int = Field(..., description="Estimated travel duration in minutes.")
    time_charge: Decimal = Field(..., description="Time component of delivery fee.")
    stop_count: int = Field(..., description="Number of delivery stops.")
    stop_fees: Decimal = Field(..., description="Aggregated stop dropoff fees.")
    delivery_charge: Decimal = Field(..., description="Subtotal delivery charge.")
    platform_fee_percent: Decimal = Field(..., description="Configured platform/service fee percentage (default 12%).")
    platform_fee: Decimal = Field(..., description="12% platform/service fee.")
    ngo_total: Decimal = Field(..., description="Total amount payable by receiving NGO (delivery charge + platform fee).")
    driver_payout: Decimal = Field(..., description="Calculated driver compensation.")
    currency: str = "INR"
