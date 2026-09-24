"""Payment Webhook, Delivery Settlement, and Refund Endpoints."""

from typing import Any, Dict
from fastapi import APIRouter, Depends, Header, Request, status
from app.api.deps import (
    get_pricing_service,
    get_settlement_service,
    get_wallet_service,
    require_admin,
    require_role,
)
from app.schemas.auth import ProfileResponse
from app.schemas.common import UserRole
from app.schemas.payment import PaymentRefundRequest, PaymentRefundResponse
from app.schemas.wallet import WalletReservationResponse
from app.services.payment_service import get_payment_provider
from app.services.pricing_service import PricingService
from app.services.settlement_service import SettlementService
from app.services.wallet_service import WalletService

router = APIRouter(tags=["Payments & Settlement"])


@router.post(
    "/payments/webhook",
    summary="Payment Gateway Webhook",
    description="Idempotent cryptographic webhook endpoint for payment provider confirmations.",
)
async def payment_webhook(
    request: Request,
    x_razorpay_signature: str = Header(default="", alias="X-Razorpay-Signature"),
) -> Dict[str, Any]:
    body = await request.body()
    provider = get_payment_provider()
    return await provider.handle_webhook(body, x_razorpay_signature)


@router.post(
    "/deliveries/{delivery_id}/reserve",
    response_model=WalletReservationResponse,
    summary="Reserve Delivery Funds",
    description="Reserves delivery charge and 12% platform fee from NGO wallet before delivery commitment.",
)
async def reserve_delivery_funds(
    delivery_id: str,
    current_profile: ProfileResponse = Depends(require_role(UserRole.RECEIVER, UserRole.ADMIN)),
    pricing_service: PricingService = Depends(get_pricing_service),
    wallet_service: WalletService = Depends(get_wallet_service),
) -> WalletReservationResponse:
    # 1. Calculate pricing breakdown and snapshot
    pricing = await pricing_service.calculate_delivery_pricing(delivery_id, snapshot=True)

    # 2. Atomically reserve the total NGO amount
    return await wallet_service.reserve_funds(
        user_id=current_profile.id,
        delivery_id=delivery_id,
        amount=pricing.ngo_total,
    )


@router.post(
    "/deliveries/{delivery_id}/settle",
    summary="Settle Completed Delivery Mission",
    description="Captures reserved NGO funds, records 12% platform fee, and credits driver payout upon delivery completion.",
)
async def settle_delivery_mission(
    delivery_id: str,
    current_profile: ProfileResponse = Depends(require_role(UserRole.DRIVER, UserRole.ADMIN)),
    settlement_service: SettlementService = Depends(get_settlement_service),
) -> Dict[str, Any]:
    return await settlement_service.settle_delivery(delivery_id)


@router.post(
    "/deliveries/{delivery_id}/refund",
    response_model=PaymentRefundResponse,
    summary="Administrative Delivery Refund",
    description="Admin-only endpoint to issue an auditable refund for a settled delivery mission back to the NGO wallet.",
)
async def refund_delivery_mission(
    delivery_id: str,
    payload: PaymentRefundRequest,
    current_admin: ProfileResponse = Depends(require_admin),
    settlement_service: SettlementService = Depends(get_settlement_service),
) -> PaymentRefundResponse:
    return await settlement_service.refund_delivery(
        delivery_id=delivery_id,
        reason=payload.reason,
        admin_user_id=current_admin.id,
        amount=payload.amount,
    )
