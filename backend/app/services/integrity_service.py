"""Food Integrity AI Analysis and Manual Review Service."""

from abc import ABC, abstractmethod
from datetime import datetime, timezone
import json
import logging
from typing import Any, Dict, List, Optional
import uuid
import httpx
from app.core.config import settings
from app.db.supabase import SupabaseClient
from app.schemas.integrity import (
    FoodIntegrityCheckResponse,
    ManualReviewRequest,
    ManualReviewStatus,
)
from app.services.audit_service import AuditService
from app.services.notification_service import NotificationService
from app.utils.exceptions import NotFoundException, ValidationException

logger = logging.getLogger("annasetu.services.integrity")


class IntegrityAnalyzer(ABC):
    """Abstract provider for visual package consistency comparison."""

    @abstractmethod
    async def analyze_package_integrity(
        self,
        pickup_image: str,
        delivery_image: str,
    ) -> Dict[str, Any]:
        """Analyzes package visual consistency.
        
        Returns:
            {
                "integrity_score": Optional[float] (0-100),
                "tampering_signal": bool,
                "reason": str,
                "available": bool
            }
        """
        pass


class GroqVisionIntegrityAnalyzer(IntegrityAnalyzer):
    """Vision-based package consistency analyzer using Groq API or graceful local heuristic."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or getattr(settings, "GROQ_API_KEY", "")

    async def analyze_package_integrity(
        self,
        pickup_image: str,
        delivery_image: str,
    ) -> Dict[str, Any]:
        # If no API key configured or unavailable, fallback gracefully without blocking
        if not self.api_key:
            logger.info("AI Vision analyzer not configured. Using deterministic fallback.")
            return {
                "integrity_score": None,
                "tampering_signal": False,
                "reason": "AI visual consistency check unavailable. Platform manual review available.",
                "available": False,
            }

        prompt = (
            "You are an auditable packaging verification assistant for food rescue logistics. "
            "Examine the two package images (pickup vs delivery) solely for visual packaging consistency, "
            "tamper seal presence, and container integrity. "
            "DO NOT assess food safety, bacterial contamination, or nutritional quality. "
            "Respond ONLY with a JSON object: "
            '{"integrity_score": <int 0-100>, "tampering_signal": <true/false>, "reason": "<neutral descriptive text>"}. '
            'Use neutral phrasing such as "No visible package discrepancy detected." or "Possible package discrepancy — manual review required."'
        )

        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                res = await client.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    json={
                        "model": "llama-3.2-11b-vision-preview",
                        "messages": [
                            {
                                "role": "user",
                                "content": [
                                    {"type": "text", "text": prompt},
                                    {"type": "image_url", "image_url": {"url": pickup_image}},
                                    {"type": "image_url", "image_url": {"url": delivery_image}},
                                ],
                            }
                        ],
                        "temperature": 0.1,
                        "response_format": {"type": "json_object"},
                    },
                )
                if res.status_code == 200:
                    data = res.json()
                    content = data["choices"][0]["message"]["content"]
                    parsed = json.loads(content)
                    return {
                        "integrity_score": float(parsed.get("integrity_score", 95)),
                        "tampering_signal": bool(parsed.get("tampering_signal", False)),
                        "reason": str(parsed.get("reason", "No visible package discrepancy detected.")),
                        "available": True,
                    }
                else:
                    logger.warning("Groq vision API error: %d %s", res.status_code, res.text)
        except Exception as exc:
            logger.warning("Groq visual analysis encountered an error: %s", exc)

        return {
            "integrity_score": None,
            "tampering_signal": False,
            "reason": "AI visual consistency check unavailable. Platform manual review available.",
            "available": False,
        }


class IntegrityService:
    """Domain service managing food integrity checks and operational reviews."""

    def __init__(
        self,
        db: SupabaseClient,
        analyzer: Optional[IntegrityAnalyzer] = None,
    ):
        self.db = db
        self.analyzer = analyzer or GroqVisionIntegrityAnalyzer()
        self.audit = AuditService(db)
        self.notification = NotificationService(db)

    async def perform_integrity_check(
        self,
        delivery_id: str,
        stop_id: Optional[str],
        pickup_image_path: str,
        delivery_image_path: str,
        seal_id: Optional[str] = None,
        pickup_seal_status: str = "INTACT",
        delivery_seal_status: str = "INTACT",
    ) -> FoodIntegrityCheckResponse:
        """Runs package comparison and records auditable food_integrity_checks."""
        ai_res = await self.analyzer.analyze_package_integrity(
            pickup_image=pickup_image_path,
            delivery_image=delivery_image_path,
        )

        # Discrepancy triggers review requirement
        tampering = bool(ai_res.get("tampering_signal", False) or delivery_seal_status in ("BROKEN", "MISSING", "DISPUTED"))
        initial_status = ManualReviewStatus.REQUIRES_ACTION if tampering else ManualReviewStatus.PENDING

        now_iso = datetime.now(timezone.utc).isoformat()
        check_id = str(uuid.uuid4())

        record_payload = {
            "id": check_id,
            "delivery_id": delivery_id,
            "stop_id": stop_id,
            "check_type": "PACKAGE_VISUAL_CONSISTENCY",
            "pickup_image_path": pickup_image_path,
            "delivery_image_path": delivery_image_path,
            "seal_id": seal_id,
            "pickup_seal_status": pickup_seal_status,
            "delivery_seal_status": delivery_seal_status,
            "ai_integrity_score": ai_res.get("integrity_score"),
            "tampering_signal": tampering,
            "ai_reason": ai_res.get("reason"),
            "manual_review_status": initial_status.value,
            "created_at": now_iso,
            "updated_at": now_iso,
        }

        created = await self.db.insert("food_integrity_checks", record_payload)

        # Audit log event
        action = "INTEGRITY_ANALYSIS_COMPLETED" if ai_res.get("available") else "INTEGRITY_ANALYSIS_FALLBACK"
        await self.audit.log_event(
            action=action,
            entity_type="food_integrity_checks",
            entity_id=check_id,
            new_values={
                "delivery_id": delivery_id,
                "tampering_signal": tampering,
                "initial_review_status": initial_status.value,
            },
        )

        # Notify if discrepancy detected
        if tampering:
            await self.audit.log_event(
                action="SEAL_DISCREPANCY_DETECTED",
                entity_type="food_integrity_checks",
                entity_id=check_id,
                new_values={"delivery_seal_status": delivery_seal_status},
            )

        return FoodIntegrityCheckResponse(**created)

    async def list_reviews(
        self,
        status: Optional[ManualReviewStatus] = None,
    ) -> List[FoodIntegrityCheckResponse]:
        """Lists integrity checks for operational manual review."""
        params = {}
        if status:
            params["manual_review_status"] = f"eq.{status.value}"
        records = await self.db.query("food_integrity_checks", params=params, order="created_at.desc")
        return [FoodIntegrityCheckResponse(**r) for r in records]

    async def submit_review(
        self,
        check_id: str,
        reviewer_id: str,
        payload: ManualReviewRequest,
    ) -> FoodIntegrityCheckResponse:
        """Admin completes manual review for an integrity check."""
        record = await self.db.get_by_id("food_integrity_checks", check_id, id_column="id")
        if not record:
            raise NotFoundException("Integrity check record not found.")

        now_iso = datetime.now(timezone.utc).isoformat()
        update_data = {
            "manual_review_status": payload.status.value,
            "reviewed_by": reviewer_id,
            "reviewed_at": now_iso,
            "updated_at": now_iso,
        }
        if payload.notes:
            update_data["review_notes"] = payload.notes

        updated = await self.db.update_by_id("food_integrity_checks", check_id, update_data)

        await self.audit.log_event(
            action="MANUAL_REVIEW_COMPLETED",
            entity_type="food_integrity_checks",
            entity_id=check_id,
            user_id=reviewer_id,
            new_values={"status": payload.status.value, "notes": payload.notes},
        )

        return FoodIntegrityCheckResponse(**updated)
