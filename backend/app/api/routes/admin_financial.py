"""Admin Financial Exceptions and Controlled Adjustments Routes."""

from typing import Any, Dict, List
from fastapi import APIRouter, Depends
from app.api.deps import get_admin_financial_service, require_admin
from app.schemas.admin_financial import (
    FinancialAdjustRequest,
    FinancialExceptionItem,
    FinancialReviewRequest,
)
from app.schemas.auth import ProfileResponse
from app.services.admin_financial_service import AdminFinancialService

router = APIRouter(prefix="/admin/financial", tags=["Admin Financial Center"])


@router.get(
    "/exceptions",
    response_model=List[FinancialExceptionItem],
    summary="List Financial Exceptions",
    description="Detects failed transactions, stale reservations, and negative balance violations.",
)
async def list_financial_exceptions(
    current_admin: ProfileResponse = Depends(require_admin),
    service: AdminFinancialService = Depends(get_admin_financial_service),
) -> List[FinancialExceptionItem]:
    return await service.list_financial_exceptions()


@router.post(
    "/{transaction_id}/review",
    response_model=Dict[str, Any],
    summary="Review Financial Exception",
    description="Records administrative review notes against a financial exception.",
)
async def review_financial_exception(
    transaction_id: str,
    payload: FinancialReviewRequest,
    current_admin: ProfileResponse = Depends(require_admin),
    service: AdminFinancialService = Depends(get_admin_financial_service),
) -> Dict[str, Any]:
    return await service.review_financial_exception(
        transaction_id=transaction_id,
        admin_id=current_admin.id,
        payload=payload,
    )


@router.post(
    "/adjust",
    response_model=Dict[str, Any],
    summary="Create Controlled Financial Adjustment",
    description="Creates an auditable ADJUSTMENT transaction and updates wallet balance without modifying historical transactions.",
)
async def create_financial_adjustment(
    payload: FinancialAdjustRequest,
    current_admin: ProfileResponse = Depends(require_admin),
    service: AdminFinancialService = Depends(get_admin_financial_service),
) -> Dict[str, Any]:
    return await service.create_adjustment(
        admin_id=current_admin.id,
        payload=payload,
    )
