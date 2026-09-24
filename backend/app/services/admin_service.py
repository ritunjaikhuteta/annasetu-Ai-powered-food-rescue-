"""Admin Platform Health, Overview Aggregation, Notifications & Audit Log Service."""

from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional
from app.core.config import settings
from app.db.supabase import SupabaseClient
from app.schemas.admin import (
    AdminOverviewResponse,
    AuditLogEntry,
    OperationalHealthStatus,
    PaginatedResponse,
    PlatformOperationalHealth,
    SystemNotification,
)
from app.services.audit_service import AuditService

logger = logging.getLogger("annasetu.services.admin")


class AdminService:
    """Operations center administration service."""

    def __init__(self, db: SupabaseClient):
        self.db = db
        self.audit = AuditService(db)

    def get_operational_health(self) -> PlatformOperationalHealth:
        """Determines operational health status without expensive queries."""
        # AI Provider health
        if not getattr(settings, "AI_ENABLED", False):
            ai_status = OperationalHealthStatus.DISABLED
        elif not getattr(settings, "GROQ_API_KEY", ""):
            ai_status = OperationalHealthStatus.DEGRADED
        else:
            ai_status = OperationalHealthStatus.AVAILABLE

        # Routing Provider health
        routing_status = OperationalHealthStatus.AVAILABLE

        # Payment Provider health
        pay_provider = getattr(settings, "PAYMENT_PROVIDER", "mock").lower()
        if pay_provider == "mock":
            pay_status = OperationalHealthStatus.MOCK
        elif getattr(settings, "RAZORPAY_KEY_ID", ""):
            pay_status = OperationalHealthStatus.AVAILABLE
        else:
            pay_status = OperationalHealthStatus.DEGRADED

        # Database health
        db_status = OperationalHealthStatus.AVAILABLE if self.db.is_configured or hasattr(self.db, "profiles") else OperationalHealthStatus.ERROR

        return PlatformOperationalHealth(
            ai_provider=ai_status,
            routing_provider=routing_status,
            payment_provider=pay_status,
            database=db_status,
        )

    async def get_overview(self) -> AdminOverviewResponse:
        """Calculates authoritative operations center metrics from database records."""
        # Active entities
        all_profiles = await self.db.query("profiles")
        active_donors = len([p for p in all_profiles if p.get("role") == "DONOR" and p.get("is_active", True)])
        active_receivers = len([p for p in all_profiles if p.get("role") == "RECEIVER" and p.get("is_active", True)])
        
        all_drivers = await self.db.query("driver_profiles")
        verified_drivers = len([d for d in all_drivers if d.get("verification_status") == "VERIFIED"])

        # Rescue items
        donations = await self.db.query("donations")
        posted_donations = len([d for d in donations if d.get("status") in ("POSTED", "MATCHED", "PARTIALLY_ALLOCATED")])

        needs = await self.db.query("ngo_needs")
        active_needs = len([n for n in needs if n.get("status") in ("ACTIVE", "PARTIALLY_FULFILLED")])

        # Deliveries
        deliveries = await self.db.query("deliveries")
        open_deliveries = len([d for d in deliveries if d.get("status") in ("OPEN", "ACCEPTED", "ASSIGNED")])
        in_transit = len([d for d in deliveries if d.get("status") in ("IN_TRANSIT", "ARRIVING_PICKUP", "PICKED_UP", "AT_STOP")])

        today_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        completed_today = len([
            d for d in deliveries
            if d.get("status") == "DELIVERED" and str(d.get("delivered_at", d.get("updated_at", ""))).startswith(today_str)
        ])

        failed = len([d for d in deliveries if d.get("status") in ("FAILED", "FAILED_PICKUP", "FAILED_DELIVERY")])
        reassign = len([d for d in deliveries if d.get("status") == "REASSIGNMENT_REQUIRED"])

        # Verifications & Integrity reviews pending
        verifications = await self.db.query("verification_records")
        pending_verif = len([v for v in verifications if v.get("status") in ("PENDING", "UNDER_REVIEW")])

        integrity_checks = await self.db.query("food_integrity_checks")
        pending_integrity = len([c for c in integrity_checks if c.get("manual_review_status") in ("PENDING", "REQUIRES_ACTION")])

        # Impact metrics
        impact_records = await self.db.query("impact_records")
        total_kg = sum(float(r.get("quantity_kg", 0.0)) for r in impact_records)
        # Fallback to delivered donations if impact_records is empty
        if total_kg == 0.0:
            total_kg = sum(float(d.get("quantity_kg", 0.0)) for d in donations if d.get("status") == "COMPLETED")

        meal_eq = int(total_kg / 0.4) if total_kg > 0 else 0
        co2_avoided = round(total_kg * 2.5, 2)

        # Financial exceptions
        transactions = await self.db.query("transactions")
        reservations = await self.db.query("wallet_reservations")
        failed_tx = len([t for t in transactions if t.get("status") == "FAILED"])
        stale_res = len([r for r in reservations if r.get("status") == "RESERVED" and r.get("is_stale")])
        financial_exceptions = failed_tx + stale_res

        return AdminOverviewResponse(
            active_donors=active_donors,
            active_receivers=active_receivers,
            verified_drivers=verified_drivers,
            posted_donations=posted_donations,
            active_needs=active_needs,
            open_deliveries=open_deliveries,
            in_transit_deliveries=in_transit,
            completed_deliveries_today=completed_today,
            pending_verifications=pending_verif,
            integrity_reviews_pending=pending_integrity,
            failed_deliveries=failed,
            reassignment_required=reassign,
            total_food_rescued_kg=total_kg,
            total_meal_equivalent=meal_eq,
            total_co2e_avoided_kg=co2_avoided,
            financial_exception_count=financial_exceptions,
            operational_health=self.get_operational_health(),
        )

    async def get_system_notifications(
        self,
        page: int = 1,
        page_size: int = 20,
    ) -> PaginatedResponse[SystemNotification]:
        """Returns system-level operational alerts and events."""
        notifications = await self.db.query("notifications")
        # Filter for system/operational notifications
        sys_notes = [
            SystemNotification(
                id=n.get("id", ""),
                type=n.get("type", "SYSTEM_ALERT"),
                title=n.get("title", "Operational Update"),
                message=n.get("message", ""),
                severity=n.get("severity", "INFO"),
                created_at=n.get("created_at", ""),
                metadata={k: v for k, v in (n.get("metadata") or {}).items() if "secret" not in k.lower() and "token" not in k.lower()},
            )
            for n in notifications
            if n.get("is_system", True) or n.get("user_id") in ("admin", "system", None)
        ]

        total = len(sys_notes)
        start = (page - 1) * page_size
        items = sys_notes[start : start + page_size]
        total_pages = (total + page_size - 1) // page_size if page_size > 0 else 1

        return PaginatedResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    async def get_audit_logs(
        self,
        actor: Optional[str] = None,
        action: Optional[str] = None,
        entity_type: Optional[str] = None,
        page: int = 1,
        page_size: int = 50,
    ) -> PaginatedResponse[AuditLogEntry]:
        """Returns append-only audit trail logs with redaction of secrets."""
        all_logs = await self.db.query("audit_logs", order="created_at.desc")

        filtered = []
        for l in all_logs:
            if actor and str(l.get("user_id")) != str(actor):
                continue
            if action and action.upper() not in str(l.get("action", "")).upper():
                continue
            if entity_type and str(l.get("entity_type", "")).lower() != entity_type.lower():
                continue

            # Redact any confidential keys in metadata
            raw_details = l.get("new_values") or l.get("details") or {}
            clean_details = {
                k: ("***REDACTED***" if any(s in k.lower() for s in ("secret", "token", "password", "key", "otp")) else v)
                for k, v in raw_details.items()
            }

            filtered.append(
                AuditLogEntry(
                    id=l.get("id", ""),
                    timestamp=l.get("created_at", ""),
                    actor=l.get("user_id") or "SYSTEM",
                    action=l.get("action", "MUTATION"),
                    entity_type=l.get("entity_type", "UNKNOWN"),
                    entity_id=l.get("entity_id"),
                    user_id=l.get("user_id"),
                    details=clean_details,
                )
            )

        total = len(filtered)
        start = (page - 1) * page_size
        items = filtered[start : start + page_size]
        total_pages = (total + page_size - 1) // page_size if page_size > 0 else 1

        return PaginatedResponse(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )
