"""Donor Subscription and Billing Endpoints."""

from typing import List, Optional
from fastapi import APIRouter, Depends, status
from app.api.deps import (
    get_subscription_service,
    require_donor,
    require_role,
)
from app.schemas.auth import ProfileResponse
from app.schemas.common import UserRole
from app.schemas.subscription import (
    SubscriptionCheckoutRequest,
    SubscriptionPlanResponse,
    SubscriptionResponse,
)
from app.services.subscription_service import SubscriptionService

router = APIRouter(tags=["Subscriptions & Billing"])


@router.get(
    "/subscription-plans",
    response_model=List[SubscriptionPlanResponse],
    summary="List Available Subscription Plans",
    description="Returns public donor subscription tiers (Starter, Business, Enterprise) with server-side prices and feature entitlements.",
)
async def list_subscription_plans(
    subscription_service: SubscriptionService = Depends(get_subscription_service),
) -> List[SubscriptionPlanResponse]:
    return await subscription_service.list_plans()


@router.get(
    "/subscription",
    response_model=Optional[SubscriptionResponse],
    summary="Get Current Donor Subscription",
    description="Fetches current subscription details, status, and renewal period for the authenticated donor.",
)
async def get_my_subscription(
    donor_profile: ProfileResponse = Depends(require_donor),
    subscription_service: SubscriptionService = Depends(get_subscription_service),
) -> Optional[SubscriptionResponse]:
    return await subscription_service.get_subscription(donor_profile.id)


@router.post(
    "/subscriptions/checkout",
    response_model=SubscriptionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Subscribe to Plan",
    description="Purchases a donor subscription tier. Prices are derived strictly server-side.",
)
async def checkout_subscription(
    payload: SubscriptionCheckoutRequest,
    donor_profile: ProfileResponse = Depends(require_donor),
    subscription_service: SubscriptionService = Depends(get_subscription_service),
) -> SubscriptionResponse:
    return await subscription_service.checkout_subscription(
        donor_user_id=donor_profile.id,
        payload=payload,
    )


@router.post(
    "/subscriptions/cancel",
    response_model=SubscriptionResponse,
    summary="Cancel Subscription",
    description="Cancels active donor subscription. Entitlements remain active until current period concludes.",
)
async def cancel_subscription(
    donor_profile: ProfileResponse = Depends(require_donor),
    subscription_service: SubscriptionService = Depends(get_subscription_service),
) -> SubscriptionResponse:
    return await subscription_service.cancel_subscription(donor_profile.id)
