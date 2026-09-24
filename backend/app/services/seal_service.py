"""Package Seal Domain Service."""

from datetime import datetime, timezone
import logging
import secrets
from typing import Any, Dict, Optional
import uuid
from app.db.supabase import SupabaseClient
from app.schemas.seal import PackageSealResponse, SealStatus
from app.utils.exceptions import NotFoundException

logger = logging.getLogger("annasetu.services.seal")


class SealService:
    """Service managing tamper-evident package seal tracking and inspection."""

    def __init__(self, db: SupabaseClient):
        self.db = db

    def generate_seal_id(self) -> str:
        """Generates a non-sequential, cryptographically unpredictable seal identifier."""
        random_suffix = secrets.token_hex(4).upper()
        return f"ANNA-{random_suffix}"

    async def create_pickup_seal(
        self,
        donation_id: str,
        delivery_id: str,
        applied_by_user_id: str,
    ) -> PackageSealResponse:
        """Applies a tamper-evident seal to a rescued food package at verified pickup."""
        seal_id = self.generate_seal_id()
        now_iso = datetime.now(timezone.utc).isoformat()

        record_id = str(uuid.uuid4())
        seal_payload = {
            "id": record_id,
            "donation_id": donation_id,
            "delivery_id": delivery_id,
            "seal_id": seal_id,
            "applied_by": applied_by_user_id,
            "applied_at": now_iso,
            "pickup_status": SealStatus.INTACT.value,
            "delivery_status": SealStatus.NOT_RECORDED.value,
            "created_at": now_iso,
            "updated_at": now_iso,
        }

        created = await self.db.insert("package_seals", seal_payload)
        logger.info("Applied package seal %s for delivery %s", seal_id, delivery_id)
        return PackageSealResponse(**created)

    async def record_delivery_seal(
        self,
        delivery_id: str,
        observed_status: SealStatus,
        notes: Optional[str] = None,
    ) -> Optional[PackageSealResponse]:
        """Records observed seal condition upon delivery handoff."""
        existing = await self.db.query("package_seals", params={"delivery_id": f"eq.{delivery_id}"})
        if not existing:
            return None

        seal_record = existing[0]
        now_iso = datetime.now(timezone.utc).isoformat()

        update_payload = {
            "delivery_status": observed_status.value,
            "verified_at": now_iso,
            "updated_at": now_iso,
        }
        if notes:
            update_payload["notes"] = notes

        updated = await self.db.update_by_id("package_seals", seal_record["id"], update_payload)
        logger.info("Recorded delivery seal condition %s for seal %s", observed_status.value, seal_record.get("seal_id"))
        return PackageSealResponse(**updated)

    async def get_seal_by_delivery(self, delivery_id: str) -> Optional[PackageSealResponse]:
        records = await self.db.query("package_seals", params={"delivery_id": f"eq.{delivery_id}"})
        if not records:
            return None
        return PackageSealResponse(**records[0])
