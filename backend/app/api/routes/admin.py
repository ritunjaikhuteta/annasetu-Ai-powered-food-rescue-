"""Admin Operations Center: Overview, Health, System Alerts, and Audit Logs."""

from typing import Optional
from fastapi import APIRouter, Depends, Query
from app.api.deps import get_admin_service, require_admin
from app.schemas.admin import (
    AdminOverviewResponse,
    AuditLogEntry,
    PaginatedResponse,
    SystemNotification,
)
from app.schemas.auth import ProfileResponse
from app.services.admin_service import AdminService

router = APIRouter(prefix="/admin", tags=["Admin Operations Center"])


@router.get(
    "/overview",
    response_model=AdminOverviewResponse,
    summary="Get Operations Command Center Overview",
    description="Returns high-density real-time operational summary metrics, active rescues, review queues, and service health.",
)
async def get_admin_overview(
    current_admin: ProfileResponse = Depends(require_admin),
    admin_service: AdminService = Depends(get_admin_service),
) -> AdminOverviewResponse:
    return await admin_service.get_overview()


@router.get(
    "/notifications/system",
    response_model=PaginatedResponse[SystemNotification],
    summary="Get System Operational Alerts",
    description="Returns system-level events and operational degradation alerts.",
)
async def get_system_notifications(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    current_admin: ProfileResponse = Depends(require_admin),
    admin_service: AdminService = Depends(get_admin_service),
) -> PaginatedResponse[SystemNotification]:
    return await admin_service.get_system_notifications(page=page, page_size=page_size)


@router.get(
    "/audit-logs",
    response_model=PaginatedResponse[AuditLogEntry],
    summary="Get Paginated Audit Logs",
    description="Returns append-only audit trail logs with confidential credentials automatically redacted.",
)
async def get_audit_logs(
    actor: Optional[str] = Query(default=None, description="Filter by actor/user ID."),
    action: Optional[str] = Query(default=None, description="Filter by action name."),
    entity_type: Optional[str] = Query(default=None, description="Filter by entity type."),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=50, ge=1, le=100),
    current_admin: ProfileResponse = Depends(require_admin),
    admin_service: AdminService = Depends(get_admin_service),
) -> PaginatedResponse[AuditLogEntry]:
    return await admin_service.get_audit_logs(
        actor=actor,
        action=action,
        entity_type=entity_type,
        page=page,
        page_size=page_size,
    )
