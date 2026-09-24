"""Admin Analytics and Platform Performance Reporting Routes."""

from fastapi import APIRouter, Depends, Query
from app.api.deps import get_admin_analytics_service, require_admin
from app.schemas.admin_analytics import (
    FinancialAnalyticsResponse,
    ImpactAnalyticsResponse,
    OperationsAnalyticsResponse,
    TimePeriod,
)
from app.schemas.auth import ProfileResponse
from app.services.admin_analytics_service import AdminAnalyticsService

router = APIRouter(prefix="/admin/analytics", tags=["Admin Analytics"])


@router.get(
    "/impact",
    response_model=ImpactAnalyticsResponse,
    summary="Get Environmental & Social Rescue Impact",
    description="Calculates rescued food weight, meal equivalents, and avoided CO2e emissions for selected timeframe.",
)
async def get_impact_analytics(
    period: str = Query(default=TimePeriod.THIRTY_DAYS.value, description="Timeframe: today, 7d, 30d, 90d, custom"),
    current_admin: ProfileResponse = Depends(require_admin),
    service: AdminAnalyticsService = Depends(get_admin_analytics_service),
) -> ImpactAnalyticsResponse:
    return await service.get_impact_analytics(period=period)


@router.get(
    "/operations",
    response_model=OperationsAnalyticsResponse,
    summary="Get Rescue Logistics Operational Efficiency",
    description="Calculates completion rates, failure rates, reassignment counts, and average delivery durations.",
)
async def get_operations_analytics(
    period: str = Query(default=TimePeriod.THIRTY_DAYS.value, description="Timeframe: today, 7d, 30d, 90d, custom"),
    current_admin: ProfileResponse = Depends(require_admin),
    service: AdminAnalyticsService = Depends(get_admin_analytics_service),
) -> OperationsAnalyticsResponse:
    return await service.get_operations_analytics(period=period)


@router.get(
    "/financial",
    response_model=FinancialAnalyticsResponse,
    summary="Get Financial & Revenue Analytics",
    description="Calculates gross delivery charges, platform service fees (12%), driver payouts, refunds, and subscription revenue.",
)
async def get_financial_analytics(
    period: str = Query(default=TimePeriod.THIRTY_DAYS.value, description="Timeframe: today, 7d, 30d, 90d, custom"),
    current_admin: ProfileResponse = Depends(require_admin),
    service: AdminAnalyticsService = Depends(get_admin_analytics_service),
) -> FinancialAnalyticsResponse:
    return await service.get_financial_analytics(period=period)
