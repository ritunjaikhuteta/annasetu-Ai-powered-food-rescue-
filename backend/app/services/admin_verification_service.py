"""Admin Verification Queue & Review Management Service."""

from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional
from app.db.supabase import SupabaseClient
from app.schemas.admin import PaginatedResponse
from app.schemas.admin_verification import (
    VerificationApproveRequest,
    VerificationDetailResponse,
    VerificationItemResponse,
    VerificationRejectRequest,
    VerificationRequestReviewRequest,
)
from app.services.audit_service import AuditService
from app.services.notification_service import NotificationService
from app.utils.exceptions import NotFoundException, ValidationException

logger = logging.getLogger("annasetu.services.admin_verification")


class AdminVerificationService:
    """Service handling manual human review and verification approvals."""

    def __init__(self, db: SupabaseClient):
        self.db = db
        self.audit = AuditService(db)
        self.notification = NotificationService(db)

    async def list_verifications(
        self,
        role: Optional[str] = None,
        verification_type: Optional[str] = None,
        status: Optional[str] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> PaginatedResponse[VerificationItemResponse]:
        """Lists verification records sorted oldest-pending-first by default."""
        params = {}
        if status:
            params["status"] = f"eq.{status}"

        # Fetch records
        records = await self.db.query("verification_records", params=params, order="created_at.asc")

        items: List[VerificationItemResponse] = []
        for r in records:
            user_id = r.get("user_id", "")
            rec_role = r.get("role") or ""

            # Filter by role if requested
            if role and rec_role.upper() != role.upper():
                continue
            if verification_type and str(r.get("verification_type", "")).upper() != verification_type.upper():
                continue

            # Fetch user name / organization
            profile = await self.db.get_by_id("profiles", user_id) or {}
            full_name = profile.get("full_name")
            org_name = None

            if rec_role == "DONOR":
                dp = await self.db.get_by_id("donor_profiles", user_id, id_column="user_id") or {}
                org_name = dp.get("business_name")
            elif rec_role == "RECEIVER":
                rp = await self.db.get_by_id("receiver_profiles", user_id, id_column="user_id") or {}
                org_name = rp.get("organization_name")
            elif rec_role == "DRIVER":
                drp = await self.db.get_by_id("driver_profiles", user_id, id_column="user_id") or {}
                org_name = f"Vehicle: {drp.get('vehicle_number', 'N/A')}"

            # Count documents
            docs = await self.db.query("verification_documents", params={"verification_id": f"eq.{r.get('id')}"})
            if not docs:
                docs = await self.db.query("verification_documents", params={"user_id": f"eq.{user_id}"})

            items.append(
                VerificationItemResponse(
                    id=r.get("id", ""),
                    user_id=user_id,
                    role=rec_role,
                    verification_type=r.get("verification_type", "ORGANIZATION_PROOF"),
                    status=r.get("status", "PENDING"),
                    created_at=r.get("created_at", ""),
                    submitted_documents_count=len(docs),
                    user_full_name=full_name,
                    organization_or_business=org_name,
                )
            )

        total = len(items)
        start = (page - 1) * page_size
        paginated_items = items[start : start + page_size]
        total_pages = (total + page_size - 1) // page_size if page_size > 0 else 1

        return PaginatedResponse(
            items=paginated_items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
        )

    async def get_verification_detail(self, verification_id: str) -> VerificationDetailResponse:
        """Retrieves full verification record with profile and documents for human review."""
        record = await self.db.get_by_id("verification_records", verification_id)
        if not record:
            raise NotFoundException(f"Verification record {verification_id} not found.")

        user_id = record.get("user_id", "")
        role = record.get("role", "")

        user_profile = await self.db.get_by_id("profiles", user_id) or {}
        role_profile = {}
        if role == "DONOR":
            role_profile = await self.db.get_by_id("donor_profiles", user_id, id_column="user_id") or {}
        elif role == "RECEIVER":
            role_profile = await self.db.get_by_id("receiver_profiles", user_id, id_column="user_id") or {}
        elif role == "DRIVER":
            role_profile = await self.db.get_by_id("driver_profiles", user_id, id_column="user_id") or {}

        docs = await self.db.query("verification_documents", params={"verification_id": f"eq.{verification_id}"})
        if not docs:
            docs = await self.db.query("verification_documents", params={"user_id": f"eq.{user_id}"})

        return VerificationDetailResponse(
            id=record.get("id", verification_id),
            user_id=user_id,
            role=role,
            verification_type=record.get("verification_type", "GENERAL"),
            status=record.get("status", "PENDING"),
            created_at=record.get("created_at", ""),
            verified_at=record.get("verified_at"),
            verified_by=record.get("verified_by"),
            rejection_reason=record.get("rejection_reason"),
            user_profile=user_profile,
            role_profile=role_profile,
            documents=docs,
        )

    async def approve_verification(
        self,
        verification_id: str,
        admin_id: str,
        payload: Optional[VerificationApproveRequest] = None,
    ) -> VerificationDetailResponse:
        """Explicit admin approval of a verification record and authoritative profile status."""
        record = await self.db.get_by_id("verification_records", verification_id)
        if not record:
            raise NotFoundException(f"Verification record {verification_id} not found.")

        user_id = record.get("user_id", "")
        role = record.get("role", "")
        now_iso = datetime.now(timezone.utc).isoformat()

        # Update verification_record
        update_payload = {
            "status": "VERIFIED",
            "verified_at": now_iso,
            "verified_by": admin_id,
            "updated_at": now_iso,
        }
        if payload and payload.review_notes:
            update_payload["notes"] = payload.review_notes

        await self.db.update_by_id("verification_records", verification_id, update_payload)

        # Update authoritative profile verification status
        if role == "DONOR":
            dp = await self.db.get_by_id("donor_profiles", user_id, id_column="user_id")
            if dp:
                await self.db.update_by_id("donor_profiles", dp["id"], {"verification_status": "VERIFIED", "updated_at": now_iso})
        elif role == "RECEIVER":
            rp = await self.db.get_by_id("receiver_profiles", user_id, id_column="user_id")
            if rp:
                await self.db.update_by_id("receiver_profiles", rp["id"], {"verification_status": "VERIFIED", "updated_at": now_iso})
        elif role == "DRIVER":
            drp = await self.db.get_by_id("driver_profiles", user_id, id_column="user_id")
            if drp:
                await self.db.update_by_id("driver_profiles", drp["id"], {"verification_status": "VERIFIED", "updated_at": now_iso})

        # Audit logging
        await self.audit.log_event(
            action="VERIFICATION_APPROVED",
            entity_type="verification_records",
            entity_id=verification_id,
            user_id=admin_id,
            new_values={"status": "VERIFIED", "role": role, "target_user": user_id},
        )

        return await self.get_verification_detail(verification_id)

    async def reject_verification(
        self,
        verification_id: str,
        admin_id: str,
        payload: VerificationRejectRequest,
    ) -> VerificationDetailResponse:
        """Explicit admin rejection of a verification record with auditable reason."""
        record = await self.db.get_by_id("verification_records", verification_id)
        if not record:
            raise NotFoundException(f"Verification record {verification_id} not found.")

        user_id = record.get("user_id", "")
        role = record.get("role", "")
        now_iso = datetime.now(timezone.utc).isoformat()

        update_payload = {
            "status": "REJECTED",
            "rejection_reason": payload.rejection_reason,
            "verified_by": admin_id,
            "updated_at": now_iso,
        }
        await self.db.update_by_id("verification_records", verification_id, update_payload)

        # Update profile status
        if role == "DONOR":
            dp = await self.db.get_by_id("donor_profiles", user_id, id_column="user_id")
            if dp:
                await self.db.update_by_id("donor_profiles", dp["id"], {"verification_status": "REJECTED", "updated_at": now_iso})
        elif role == "RECEIVER":
            rp = await self.db.get_by_id("receiver_profiles", user_id, id_column="user_id")
            if rp:
                await self.db.update_by_id("receiver_profiles", rp["id"], {"verification_status": "REJECTED", "updated_at": now_iso})
        elif role == "DRIVER":
            drp = await self.db.get_by_id("driver_profiles", user_id, id_column="user_id")
            if drp:
                await self.db.update_by_id("driver_profiles", drp["id"], {"verification_status": "REJECTED", "updated_at": now_iso})

        # Audit logging
        await self.audit.log_event(
            action="VERIFICATION_REJECTED",
            entity_type="verification_records",
            entity_id=verification_id,
            user_id=admin_id,
            new_values={"status": "REJECTED", "role": role, "reason": payload.rejection_reason},
        )

        return await self.get_verification_detail(verification_id)

    async def request_review(
        self,
        verification_id: str,
        admin_id: str,
        payload: VerificationRequestReviewRequest,
    ) -> VerificationDetailResponse:
        """Sets verification record into UNDER_REVIEW state."""
        record = await self.db.get_by_id("verification_records", verification_id)
        if not record:
            raise NotFoundException(f"Verification record {verification_id} not found.")

        now_iso = datetime.now(timezone.utc).isoformat()
        update_payload = {
            "status": "UNDER_REVIEW",
            "notes": payload.review_notes,
            "updated_at": now_iso,
        }
        await self.db.update_by_id("verification_records", verification_id, update_payload)

        await self.audit.log_event(
            action="VERIFICATION_REQUEST_REVIEW",
            entity_type="verification_records",
            entity_id=verification_id,
            user_id=admin_id,
            new_values={"status": "UNDER_REVIEW", "notes": payload.review_notes},
        )

        return await self.get_verification_detail(verification_id)
