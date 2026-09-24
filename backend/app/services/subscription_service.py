"""Donor Subscription and Entitlement Management Service."""

from datetime import datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP
import logging
from typing import Any, Dict, List, Optional
import uuid
from app.db.supabase import SupabaseClient
from app.schemas.subscription import (
    BillingCycle,
    SubscriptionCheckoutRequest,
    SubscriptionPlanResponse,
    SubscriptionResponse,
    SubscriptionStatus,
)
from app.services.audit_service import AuditService
from app.services.notification_service import NotificationService
from app.utils.exceptions import ConflictException, NotFoundException, ValidationException

logger = logging.getLogger("annasetu.services.subscription")

TWO_PLACES = Decimal("0.01")


class SubscriptionService:
    """Service managing donor subscription tiers, checkout, billing cycles, and entitlements."""

    # Seeded platform default subscription plans
    DEFAULT_PLANS = [
        {
            "id": "plan-starter",
            "name": "Starter",
            "code": "starter",
            "monthly_price": Decimal("0.00"),
            "yearly_price": Decimal("0.00"),
            "currency": "INR",
            "features": {
                "max_monthly_rescues": 10,
                "basic_reporting": True,
                "impact_certificates": True,
                "dedicated_support": False,
                "custom_analytics": False,
            },
            "is_active": True,
        },
        {
            "id": "plan-business",
            "name": "Business",
            "code": "business",
            "monthly_price": Decimal("1499.00"),
            "yearly_price": Decimal("14990.00"),
            "currency": "INR",
            "features": {
                "max_monthly_rescues": 100,
                "basic_reporting": True,
                "impact_certificates": True,
                "priority_dispatch": True,
                "dedicated_support": True,
                "custom_analytics": False,
            },
            "is_active": True,
        },
        {
            "id": "plan-enterprise",
            "name": "Enterprise",
            "code": "enterprise",
            "monthly_price": Decimal("4999.00"),
            "yearly_price": Decimal("49990.00"),
            "currency": "INR",
            "features": {
                "max_monthly_rescues": 99999,
                "basic_reporting": True,
                "impact_certificates": True,
                "priority_dispatch": True,
                "dedicated_support": True,
                "custom_analytics": True,
                "api_access": True,
            },
            "is_active": True,
        },
    ]

    def __init__(self, db: SupabaseClient):
        self.db = db
        self.audit = AuditService(db)
        self.notification = NotificationService(db)

    async def list_plans(self) -> List[SubscriptionPlanResponse]:
        """Returns available subscription tiers from database or seeded defaults."""
        db_plans = await self.db.query("subscription_plans", params={"is_active": "eq.true"})
        if db_plans:
            return [
                SubscriptionPlanResponse(
                    id=p["id"],
                    name=p["name"],
                    code=p.get("code", p["name"].lower()),
                    monthly_price=Decimal(str(p.get("monthly_price", "0.00"))).quantize(TWO_PLACES, rounding=ROUND_HALF_UP),
                    yearly_price=Decimal(str(p.get("yearly_price", "0.00"))).quantize(TWO_PLACES, rounding=ROUND_HALF_UP),
                    currency=p.get("currency", "INR"),
                    features=p.get("features", {}),
                    is_active=p.get("is_active", True),
                )
                for p in db_plans
            ]

        return [
            SubscriptionPlanResponse(
                id=p["id"],
                name=p["name"],
                code=p["code"],
                monthly_price=p["monthly_price"],
                yearly_price=p["yearly_price"],
                currency=p["currency"],
                features=p["features"],
                is_active=p["is_active"],
            )
            for p in self.DEFAULT_PLANS
        ]

    async def get_plan_by_id(self, plan_id: str) -> Dict[str, Any]:
        """Finds a plan by ID or code."""
        db_plan = await self.db.get_by_id("subscription_plans", plan_id, id_column="id")
        if db_plan:
            return db_plan
        for p in self.DEFAULT_PLANS:
            if p["id"] == plan_id or p["code"] == plan_id:
                return p
        raise NotFoundException(f"Subscription plan '{plan_id}' not found.")

    async def get_subscription(self, donor_user_id: str) -> Optional[SubscriptionResponse]:
        """Fetches active subscription for donor."""
        subs = await self.db.query(
            "subscriptions",
            params={"user_id": f"eq.{donor_user_id}"},
            order="created_at.desc",
        )
        if not subs:
            return None
        sub = subs[0]
        plan = await self.get_plan_by_id(sub["plan_id"])
        return SubscriptionResponse(
            id=sub["id"],
            user_id=sub["user_id"],
            plan_id=sub["plan_id"],
            plan_name=plan.get("name", "Donor Plan"),
            billing_cycle=BillingCycle(sub.get("billing_cycle", "MONTHLY")),
            amount=Decimal(str(sub.get("amount", "0.00"))).quantize(TWO_PLACES, rounding=ROUND_HALF_UP),
            status=SubscriptionStatus(sub.get("status", "ACTIVE")),
            current_period_start=sub["current_period_start"],
            current_period_end=sub["current_period_end"],
            created_at=sub.get("created_at"),
            updated_at=sub.get("updated_at"),
        )

    async def checkout_subscription(
        self,
        donor_user_id: str,
        payload: SubscriptionCheckoutRequest,
    ) -> SubscriptionResponse:
        """Activates a donor subscription plan. Derives plan pricing strictly server-side."""
        plan = await self.get_plan_by_id(payload.plan_id)

        # Derive price server-side — NEVER trust client prices
        is_yearly = payload.billing_cycle == BillingCycle.YEARLY
        price = Decimal(str(plan["yearly_price"] if is_yearly else plan["monthly_price"])).quantize(TWO_PLACES, rounding=ROUND_HALF_UP)

        now = datetime.now(timezone.utc)
        period_days = 365 if is_yearly else 30
        period_end = now + timedelta(days=period_days)

        sub_id = str(uuid.uuid4())
        now_iso = now.isoformat()

        record = {
            "id": sub_id,
            "user_id": donor_user_id,
            "plan_id": plan["id"],
            "billing_cycle": payload.billing_cycle.value,
            "amount": float(price),
            "status": SubscriptionStatus.ACTIVE.value,
            "current_period_start": now_iso,
            "current_period_end": period_end.isoformat(),
            "created_at": now_iso,
            "updated_at": now_iso,
        }

        created = await self.db.insert("subscriptions", record)

        await self.audit.log_event(
            action="SUBSCRIPTION_ACTIVATED",
            entity_type="subscriptions",
            entity_id=sub_id,
            user_id=donor_user_id,
            new_values={"plan_id": plan["id"], "cycle": payload.billing_cycle.value, "amount": float(price)},
        )

        await self.notification.notify_event(
            user_id=donor_user_id,
            event_type="SUBSCRIPTION_ACTIVATED",
            title="Subscription Active",
            message=f"You are now subscribed to the AnnaSetu {plan['name']} plan ({payload.billing_cycle.value}).",
            data={"subscription_id": sub_id, "plan_id": plan["id"]},
        )

        return SubscriptionResponse(
            id=sub_id,
            user_id=donor_user_id,
            plan_id=plan["id"],
            plan_name=plan["name"],
            billing_cycle=payload.billing_cycle,
            amount=price,
            status=SubscriptionStatus.ACTIVE,
            current_period_start=now_iso,
            current_period_end=period_end.isoformat(),
            created_at=now_iso,
        )

    async def cancel_subscription(self, donor_user_id: str) -> SubscriptionResponse:
        """Cancels donor subscription while preserving historical records."""
        sub = await self.get_subscription(donor_user_id)
        if not sub:
            raise NotFoundException("No active subscription found to cancel.")

        if sub.status == SubscriptionStatus.CANCELLED:
            raise ConflictException("Subscription is already cancelled.")

        now_iso = datetime.now(timezone.utc).isoformat()
        updated = await self.db.update_by_id(
            "subscriptions",
            sub.id,
            {"status": SubscriptionStatus.CANCELLED.value, "updated_at": now_iso},
        )

        await self.audit.log_event(
            action="SUBSCRIPTION_CANCELLED",
            entity_type="subscriptions",
            entity_id=sub.id,
            user_id=donor_user_id,
        )

        await self.notification.notify_event(
            user_id=donor_user_id,
            event_type="SUBSCRIPTION_CANCELLED",
            title="Subscription Cancelled",
            message="Your AnnaSetu subscription has been cancelled. Active benefits will remain until the period ends.",
            data={"subscription_id": sub.id},
        )

        return await self.get_subscription(donor_user_id)  # type: ignore

    async def has_feature(self, donor_user_id: str, feature_key: str) -> bool:
        """Entitlement check: determines if donor's active tier grants a specific capability."""
        sub = await self.get_subscription(donor_user_id)
        plan_id = sub.plan_id if (sub and sub.status == SubscriptionStatus.ACTIVE) else "plan-starter"
        plan = await self.get_plan_by_id(plan_id)
        features = plan.get("features", {})
        return bool(features.get(feature_key, False))
