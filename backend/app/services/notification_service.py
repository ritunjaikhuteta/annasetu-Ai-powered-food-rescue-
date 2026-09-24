"""Notification Service for deterministic system events."""

import logging
import uuid
from typing import Any, Dict, Optional
from app.db.supabase import SupabaseClient

logger = logging.getLogger("annasetu.services.notification")


class NotificationService:
    """Service managing deterministic notifications in the notifications table."""

    def __init__(self, db: SupabaseClient):
        self.db = db

    async def notify_receiver_match(
        self,
        receiver_user_id: str,
        match_id: str,
        donation_id: str,
        fulfillable_quantity_kg: float,
        diet_type: str,
        priority_label: str,
    ) -> Optional[Dict[str, Any]]:
        """Create a notification for high/medium priority rescue matches if not already notified."""
        if priority_label not in ("HIGH", "MEDIUM"):
            return None

        # Check existing notification to avoid duplicate spam on recalculation
        existing = await self.db.query(
            "notifications",
            params={
                "user_id": f"eq.{receiver_user_id}",
                "type": "eq.MATCH",
            },
        )
        for item in existing:
            data = item.get("data") or {}
            if data.get("match_id") == match_id or data.get("donation_id") == donation_id:
                logger.info("Notification already delivered for match %s to user %s", match_id, receiver_user_id)
                return item

        diet_desc = diet_type.lower().replace("_", "-")
        title = "New rescue opportunity"
        message = (
            f"{fulfillable_quantity_kg:.1f} kg of {diet_desc} surplus food is available nearby "
            f"and can reach your center before the rescue deadline."
        )

        notification_payload = {
            "id": str(uuid.uuid4()),
            "user_id": receiver_user_id,
            "type": "MATCH",
            "title": title,
            "message": message,
            "data": {
                "match_id": match_id,
                "donation_id": donation_id,
                "priority_label": priority_label,
            },
            "is_read": False,
        }

        try:
            return await self.db.insert("notifications", notification_payload)
        except Exception as exc:
            logger.warning("Failed to persist notification: %s", exc)
            return None

    async def notify_event(
        self,
        user_id: str,
        event_type: str,
        title: str,
        message: str,
        data: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        """Creates a deterministic event notification for delivery lifecycle with deduplication."""
        data_payload = data or {}
        delivery_id = data_payload.get("delivery_id")

        if delivery_id:
            existing = await self.db.query(
                "notifications",
                params={
                    "user_id": f"eq.{user_id}",
                    "type": f"eq.{event_type}",
                },
            )
            for item in existing:
                item_data = item.get("data") or {}
                if item_data.get("delivery_id") == delivery_id and item_data.get("event_key") == data_payload.get("event_key"):
                    logger.info("Notification %s already sent to user %s for delivery %s", event_type, user_id, delivery_id)
                    return item

        notification_payload = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "type": event_type,
            "title": title,
            "message": message,
            "data": data_payload,
            "is_read": False,
        }

        try:
            return await self.db.insert("notifications", notification_payload)
        except Exception as exc:
            logger.warning("Failed to persist event notification %s: %s", event_type, exc)
            return None

