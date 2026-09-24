"""Handoff Verification, Seal, and Evidence API Endpoints."""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from app.api.deps import (
    get_handoff_service,
    require_driver,
    require_role,
    require_verified_role,
)
from app.schemas.common import UserRole
from app.schemas.delivery import DeliveryResponse
from app.schemas.evidence import (
    DeliveryEvidenceRequest,
    HandoffEvidenceResponse,
    PickupEvidenceRequest,
)
from app.schemas.handoff import (
    HandoffVerificationRequest,
    OTPGenerationResponse,
)
from app.schemas.seal import SealStatus
from app.schemas.auth import ProfileResponse
from app.services.handoff_service import HandoffService

router = APIRouter(tags=["Handoff Verification"])


# ─── PICKUP ENDPOINTS ────────────────────────────────────────────────────────

@router.post(
    "/deliveries/{delivery_id}/pickup-otp",
    response_model=OTPGenerationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate Pickup Verification OTP",
    description="Generates a single-use OTP for the donor to share with the delivery partner upon arrival.",
)
async def generate_pickup_otp(
    delivery_id: str,
    current_profile: ProfileResponse = Depends(require_role(UserRole.DONOR, UserRole.ADMIN)),
    handoff_service: HandoffService = Depends(get_handoff_service),
) -> OTPGenerationResponse:
    return await handoff_service.generate_pickup_otp(
        delivery_id=delivery_id,
        caller_user_id=current_profile.id,
        caller_role=current_profile.role.value,
    )


@router.post(
    "/deliveries/{delivery_id}/verify-pickup",
    response_model=DeliveryResponse,
    summary="Verify Food Pickup Handoff",
    description="Driver verifies pickup using donor OTP with deterministic GPS proximity check.",
)
async def verify_pickup(
    delivery_id: str,
    payload: HandoffVerificationRequest,
    driver_profile: ProfileResponse = Depends(require_driver),
    handoff_service: HandoffService = Depends(get_handoff_service),
) -> DeliveryResponse:
    return await handoff_service.verify_pickup(
        delivery_id=delivery_id,
        driver_user_id=driver_profile.id,
        payload=payload,
    )


@router.post(
    "/deliveries/{delivery_id}/pickup-evidence",
    response_model=List[HandoffEvidenceResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Upload Pickup Evidence Photos",
    description="Assigned driver uploads package and applied tamper seal photos.",
)
async def upload_pickup_evidence(
    delivery_id: str,
    payload: PickupEvidenceRequest,
    driver_profile: ProfileResponse = Depends(require_driver),
    handoff_service: HandoffService = Depends(get_handoff_service),
) -> List[HandoffEvidenceResponse]:
    return await handoff_service.record_pickup_evidence(
        delivery_id=delivery_id,
        driver_user_id=driver_profile.id,
        payload=payload,
    )


# ─── DELIVERY STOP ENDPOINTS ─────────────────────────────────────────────────

@router.post(
    "/deliveries/{delivery_id}/stops/{stop_id}/delivery-otp",
    response_model=OTPGenerationResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Generate Delivery Stop Verification OTP",
    description="Receiver generates a single-use OTP for the delivery stop to share with the partner upon arrival.",
)
async def generate_delivery_otp(
    delivery_id: str,
    stop_id: str,
    current_profile: ProfileResponse = Depends(require_role(UserRole.RECEIVER, UserRole.ADMIN)),
    handoff_service: HandoffService = Depends(get_handoff_service),
) -> OTPGenerationResponse:
    return await handoff_service.generate_delivery_otp(
        delivery_id=delivery_id,
        stop_id=stop_id,
        caller_user_id=current_profile.id,
        caller_role=current_profile.role.value,
    )


@router.post(
    "/deliveries/{delivery_id}/stops/{stop_id}/verify-delivery",
    response_model=DeliveryResponse,
    summary="Verify Food Delivery Handoff",
    description="Driver verifies stop handoff using receiver OTP with GPS proximity and seal inspection.",
)
async def verify_delivery(
    delivery_id: str,
    stop_id: str,
    payload: HandoffVerificationRequest,
    seal_condition: Optional[SealStatus] = Query(default=SealStatus.INTACT, description="Observed tamper seal status."),
    driver_profile: ProfileResponse = Depends(require_driver),
    handoff_service: HandoffService = Depends(get_handoff_service),
) -> DeliveryResponse:
    return await handoff_service.verify_delivery(
        delivery_id=delivery_id,
        stop_id=stop_id,
        driver_user_id=driver_profile.id,
        payload=payload,
        seal_condition=seal_condition,
    )


@router.post(
    "/deliveries/{delivery_id}/stops/{stop_id}/delivery-evidence",
    response_model=List[HandoffEvidenceResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Upload Delivery Evidence Photos",
    description="Driver uploads package and seal photos upon arrival at delivery stop, triggering visual integrity check.",
)
async def upload_delivery_evidence(
    delivery_id: str,
    stop_id: str,
    payload: DeliveryEvidenceRequest,
    driver_profile: ProfileResponse = Depends(require_driver),
    handoff_service: HandoffService = Depends(get_handoff_service),
) -> List[HandoffEvidenceResponse]:
    return await handoff_service.record_delivery_evidence(
        delivery_id=delivery_id,
        stop_id=stop_id,
        driver_user_id=driver_profile.id,
        payload=payload,
    )


@router.get(
    "/deliveries/{delivery_id}/evidence",
    response_model=List[HandoffEvidenceResponse],
    summary="Get Delivery Handoff Evidence",
    description="Fetches access-controlled handoff evidence photos for authorized participants.",
)
async def get_delivery_evidence(
    delivery_id: str,
    current_profile: ProfileResponse = Depends(require_role(UserRole.DONOR, UserRole.RECEIVER, UserRole.DRIVER, UserRole.ADMIN)),
    handoff_service: HandoffService = Depends(get_handoff_service),
) -> List[HandoffEvidenceResponse]:
    return await handoff_service.get_evidence(
        delivery_id=delivery_id,
        user_id=current_profile.id,
        user_role=current_profile.role.value,
    )
