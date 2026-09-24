"""Admin schemas for platform overview, system notifications, audit logs, and pagination."""

from enum import Enum
from typing import Any, Dict, Generic, List, Optional, TypeVar
from pydantic import BaseModel, Field

T = TypeVar("T")


class OperationalHealthStatus(str, Enum):
    AVAILABLE = "AVAILABLE"
    DEGRADED = "DEGRADED"
    DISABLED = "DISABLED"
    MOCK = "MOCK"
    FALLBACK = "FALLBACK"
    ERROR = "ERROR"


class PlatformOperationalHealth(BaseModel):
    ai_provider: OperationalHealthStatus
    routing_provider: OperationalHealthStatus
    payment_provider: OperationalHealthStatus
    database: OperationalHealthStatus


class AdminOverviewResponse(BaseModel):
    # User and entity counts
    active_donors: int
    active_receivers: int
    verified_drivers: int

    # Core rescue activity
    posted_donations: int
    active_needs: int

    # Deliveries
    open_deliveries: int
    in_transit_deliveries: int
    completed_deliveries_today: int

    # Review queues
    pending_verifications: int
    integrity_reviews_pending: int

    # Exceptions
    failed_deliveries: int
    reassignment_required: int

    # Impact metrics
    total_food_rescued_kg: float
    total_meal_equivalent: int
    total_co2e_avoided_kg: float

    # Financial exceptions
    financial_exception_count: int

    # Operational status
    operational_health: PlatformOperationalHealth


class SystemNotification(BaseModel):
    id: str
    type: str
    title: str
    message: str
    severity: str  # INFO, WARNING, ERROR, CRITICAL
    created_at: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AuditLogEntry(BaseModel):
    id: str
    timestamp: str
    actor: str
    action: str
    entity_type: str
    entity_id: Optional[str] = None
    user_id: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)


class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int
