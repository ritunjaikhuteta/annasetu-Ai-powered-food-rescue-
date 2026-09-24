"""Digital Wallet and Financial Ledger Endpoints."""

from typing import List
from fastapi import APIRouter, Depends, status
from app.api.deps import (
    get_current_profile,
    get_wallet_service,
    require_role,
)
from app.schemas.auth import ProfileResponse
from app.schemas.common import UserRole
from app.schemas.wallet import (
    TransactionResponse,
    WalletResponse,
    WalletTopUpRequest,
    WalletTopUpResponse,
)
from app.services.wallet_service import WalletService

router = APIRouter(prefix="/wallet", tags=["Wallet & Ledger"])


@router.get(
    "",
    response_model=WalletResponse,
    summary="Get Current User Wallet",
    description="Fetches balance, reserved funds, and available balance for the authenticated receiver or partner.",
)
async def get_my_wallet(
    current_profile: ProfileResponse = Depends(require_role(UserRole.RECEIVER, UserRole.DRIVER, UserRole.ADMIN)),
    wallet_service: WalletService = Depends(get_wallet_service),
) -> WalletResponse:
    return await wallet_service.get_wallet(current_profile.id)


@router.get(
    "/transactions",
    response_model=List[TransactionResponse],
    summary="Get Wallet Transaction Ledger",
    description="Returns auditable financial transactions for the authenticated user's wallet.",
)
async def get_wallet_transactions(
    current_profile: ProfileResponse = Depends(require_role(UserRole.RECEIVER, UserRole.DRIVER, UserRole.ADMIN)),
    wallet_service: WalletService = Depends(get_wallet_service),
) -> List[TransactionResponse]:
    return await wallet_service.list_transactions(current_profile.id)


@router.post(
    "/top-up",
    response_model=WalletTopUpResponse,
    status_code=status.HTTP_200_OK,
    summary="Top-Up Wallet Funds",
    description="Credits wallet balance using simulated demo payment or real payment gateway.",
)
async def top_up_wallet(
    payload: WalletTopUpRequest,
    current_profile: ProfileResponse = Depends(require_role(UserRole.RECEIVER, UserRole.ADMIN)),
    wallet_service: WalletService = Depends(get_wallet_service),
) -> WalletTopUpResponse:
    return await wallet_service.top_up_wallet(
        user_id=current_profile.id,
        amount=payload.amount,
        idempotency_key=payload.idempotency_key,
    )
