"""Delivery Pricing and Financial Breakdown Endpoints."""

from fastapi import APIRouter, Depends
from app.api.deps import get_pricing_service, require_role
from app.schemas.auth import ProfileResponse
from app.schemas.common import UserRole
from app.schemas.pricing import DeliveryPricingResponse
from app.services.pricing_service import PricingService

router = APIRouter(prefix="/pricing", tags=["Pricing & Rates"])


@router.get(
    "/delivery/{delivery_id}",
    response_model=DeliveryPricingResponse,
    summary="Calculate Delivery Pricing Breakdown",
    description="Calculates delivery charge, 12% platform fee, NGO total, and driver payout using Decimal arithmetic.",
)
async def get_delivery_pricing(
    delivery_id: str,
    current_profile: ProfileResponse = Depends(require_role(UserRole.DONOR, UserRole.RECEIVER, UserRole.DRIVER, UserRole.ADMIN)),
    pricing_service: PricingService = Depends(get_pricing_service),
) -> DeliveryPricingResponse:
    return await pricing_service.calculate_delivery_pricing(delivery_id)
