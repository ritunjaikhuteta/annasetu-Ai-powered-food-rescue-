"""Audit Logging Service."""

import logging
import uuid
from typing import Any, Dict, Optional
from app.db.supabase import SupabaseClient

logger = logging.getLogger("annasetu.services.audit")


class AuditService:
    """Service writing tamper-evident mutation records to audit_logs."""

    def __init__(self, db: SupabaseClient):
        self.db = db

    async def log_event(
        self,
        action: str,
        entity_type: str,
        entity_id: str,
        user_id: Optional[str] = None,
        old_values: Optional[Dict[str, Any]] = None,
        new_values: Optional[Dict[str, Any]] = None,
        ip_address: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """Record an internal audit event."""
        payload = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "action": action,
            "entity_type": entity_type,
            "entity_id": entity_id,
            "old_values": old_values,
            "new_values": new_values,
            "ip_address": ip_address,
        }

        try:
            return await self.db.insert("audit_logs", payload)
        except Exception as exc:
            logger.warning("Audit logging warning for %s on %s:%s: %s", action, entity_type, entity_id, exc)
            return None
