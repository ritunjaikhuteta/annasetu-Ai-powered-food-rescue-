"""Handoff Verification, Seal, and Evidence Domain Service."""

from datetime import datetime, timezone
import logging
from typing import Any, Dict, List, Optional
import uuid
from app.db.supabase import SupabaseClient
from app.schemas.delivery import DeliveryResponse, DeliveryStatus, DeliveryStopStatus, DeliveryStopType
from app.schemas.driver import DriverAvailabilityStatus
from app.schemas.evidence import (
    DeliveryEvidenceRequest,
    EvidenceType,
    HandoffEvidenceResponse,
    PickupEvidenceRequest,
)
from app.schemas.handoff import (
    HandoffStatus,
    HandoffType,
    HandoffVerificationRequest,
    HandoffVerificationResponse,
    OTPGenerationResponse,
)
from app.schemas.seal import PackageSealResponse, SealStatus
from app.services.audit_service import AuditService
from app.services.driver_service import DriverService
from app.services.integrity_service import IntegrityService
from app.services.notification_service import NotificationService
from app.services.otp_service import OTPService
from app.services.routing_provider import RoutingProvider, get_routing_provider
from app.services.seal_service import SealService
from app.utils.exceptions import ConflictException, ForbiddenException, NotFoundException, ValidationException

logger = logging.getLogger("annasetu.services.handoff")


class HandoffService:
    """Core domain service managing OTP handoffs, tamper seals, evidence tracking, and integrity."""

    PICKUP_PROXIMITY_RADIUS_KM = 0.30    # 300 meters
    DELIVERY_PROXIMITY_RADIUS_KM = 0.30  # 300 meters

    def __init__(
        self,
        db: SupabaseClient,
        routing: Optional[RoutingProvider] = None,
        otp_service: Optional[OTPService] = None,
        seal_service: Optional[SealService] = None,
        integrity_service: Optional[IntegrityService] = None,
    ):
        self.db = db
        self.routing = routing or get_routing_provider()
        self.otp_service = otp_service or OTPService()
        self.seal_service = seal_service or SealService(db)
        self.integrity_service = integrity_service or IntegrityService(db)
        self.driver_service = DriverService(db, self.routing)
        self.notification = NotificationService(db)
        self.audit = AuditService(db)

    async def _get_delivery_with_stops(self, delivery_id: str) -> Dict[str, Any]:
        delivery = await self.db.get_by_id("deliveries", delivery_id, id_column="id")
        if not delivery:
            raise NotFoundException("Delivery not found.", error_code="DELIVERY_NOT_FOUND")

        stops = await self.db.query(
            "delivery_stops",
            params={"delivery_id": f"eq.{delivery_id}"},
            order="sequence_number.asc",
        )
        delivery["stops"] = stops
        return delivery

    # ─── PICKUP OTP ─────────────────────────────────────────────────────────

    async def generate_pickup_otp(
        self,
        delivery_id: str,
        caller_user_id: str,
        caller_role: str,
    ) -> OTPGenerationResponse:
        """Generates single-use pickup verification OTP for the donor to share with the driver."""
        delivery = await self._get_delivery_with_stops(delivery_id)
        donation = await self.db.get_by_id("donations", delivery["donation_id"], id_column="id")
        if not donation:
            raise NotFoundException("Donation record not found.")

        # Access check: donor who owns the donation or admin
        if caller_role != "ADMIN" and donation.get("donor_id") != caller_user_id:
            raise ForbiddenException("Only the donating organization can request the pickup OTP.")

        # Find pickup stop
        pickup_stop = next((s for s in delivery["stops"] if s["stop_type"] == DeliveryStopType.PICKUP.value), None)
        stop_id = pickup_stop["id"] if pickup_stop else None

        # Invalidate any older active pending OTP for this delivery pickup
        existing_otps = await self.db.query(
            "handoff_verifications",
            params={
                "delivery_id": f"eq.{delivery_id}",
                "handoff_type": f"eq.{HandoffType.PICKUP.value}",
                "status": f"eq.{HandoffStatus.PENDING.value}",
            },
        )
        for old in existing_otps:
            await self.db.update_by_id("handoff_verifications", old["id"], {"status": HandoffStatus.EXPIRED.value})

        # Generate new OTP
        plaintext_otp, otp_hash, expires_at = self.otp_service.generate_otp()
        record_id = str(uuid.uuid4())
        now_iso = datetime.now(timezone.utc).isoformat()

        record = {
            "id": record_id,
            "delivery_id": delivery_id,
            "stop_id": stop_id,
            "handoff_type": HandoffType.PICKUP.value,
            "otp_hash": otp_hash,
            "attempts": 0,
            "max_attempts": self.otp_service.max_attempts,
            "expires_at": expires_at.isoformat(),
            "status": HandoffStatus.PENDING.value,
            "created_at": now_iso,
            "updated_at": now_iso,
        }

        await self.db.insert("handoff_verifications", record)

        await self.audit.log_event(
            action="PICKUP_OTP_ISSUED",
            entity_type="deliveries",
            entity_id=delivery_id,
            user_id=caller_user_id,
            new_values={"handoff_id": record_id, "expires_at": expires_at.isoformat()},
        )

        return OTPGenerationResponse(
            delivery_id=delivery_id,
            stop_id=stop_id,
            handoff_type=HandoffType.PICKUP,
            otp=plaintext_otp,
            expires_at=expires_at.isoformat(),
        )

    async def verify_pickup(
        self,
        delivery_id: str,
        driver_user_id: str,
        payload: HandoffVerificationRequest,
    ) -> DeliveryResponse:
        """Driver verifies pickup using donor-supplied OTP with GPS proximity validation."""
        delivery = await self._get_delivery_with_stops(delivery_id)
        driver_prof = await self.driver_service.get_driver_profile(driver_user_id)

        # 1. Driver assignment check
        if delivery.get("driver_id") != driver_prof.id:
            raise ForbiddenException("You are not the assigned delivery partner for this mission.")

        # 2. State machine check
        if delivery.get("status") not in (DeliveryStatus.ARRIVING_PICKUP.value, DeliveryStatus.ACCEPTED.value):
            raise ConflictException(
                f"Delivery must be at pickup stage (current: {delivery.get('status')}).",
                error_code="INVALID_DELIVERY_STATE",
            )

        # 3. Pickup stop
        pickup_stop = next((s for s in delivery["stops"] if s["stop_type"] == DeliveryStopType.PICKUP.value), None)
        if not pickup_stop:
            raise NotFoundException("Pickup stop record not found.")

        # 4. GPS proximity check
        loc = await self.db.get_by_id("locations", pickup_stop["location_id"], id_column="id")
        if loc:
            p_lat = float(loc.get("latitude", 28.6139))
            p_lon = float(loc.get("longitude", 77.2090))
            dist = self.routing.calculate_distance(payload.latitude, payload.longitude, p_lat, p_lon)
            if dist > self.PICKUP_PROXIMITY_RADIUS_KM:
                logger.warning("Driver GPS (%.4f, %.4f) is %.2f km from pickup (limit: 0.3 km)", payload.latitude, payload.longitude, dist)
                raise ConflictException(
                    f"Driver is outside the pickup proximity radius ({int(dist * 1000)}m > 300m).",
                    error_code="PROXIMITY_CHECK_FAILED",
                )

        # 5. Fetch active pending OTP record
        otps = await self.db.query(
            "handoff_verifications",
            params={
                "delivery_id": f"eq.{delivery_id}",
                "handoff_type": f"eq.{HandoffType.PICKUP.value}",
                "status": f"eq.{HandoffStatus.PENDING.value}",
            },
            order="created_at.desc",
            limit=1,
        )
        if not otps:
            raise ConflictException("Invalid or expired verification code.", error_code="OTP_VERIFICATION_FAILED")

        handoff_rec = otps[0]
        verif_result = self.otp_service.verify_otp(
            candidate_otp=payload.otp,
            stored_hash=handoff_rec["otp_hash"],
            expires_at_iso=handoff_rec["expires_at"],
            current_attempts=int(handoff_rec.get("attempts", 0)),
        )

        now_iso = datetime.now(timezone.utc).isoformat()

        if not verif_result["is_valid"]:
            # Update attempts and status
            upd = {"attempts": verif_result["new_attempts"], "updated_at": now_iso}
            if verif_result["attempts_exceeded"] or verif_result["is_expired"]:
                upd["status"] = HandoffStatus.FAILED.value if verif_result["attempts_exceeded"] else HandoffStatus.EXPIRED.value

            await self.db.update_by_id("handoff_verifications", handoff_rec["id"], upd)

            await self.audit.log_event(
                action="PICKUP_OTP_FAILED",
                entity_type="handoff_verifications",
                entity_id=handoff_rec["id"],
                user_id=driver_user_id,
                new_values={"attempts": verif_result["new_attempts"]},
            )
            raise ConflictException("Invalid or expired verification code.", error_code="OTP_VERIFICATION_FAILED")

        # Success: Mark handoff VERIFIED
        await self.db.update_by_id(
            "handoff_verifications",
            handoff_rec["id"],
            {
                "status": HandoffStatus.VERIFIED.value,
                "verified_by": driver_prof.id,
                "verified_at": now_iso,
                "latitude": payload.latitude,
                "longitude": payload.longitude,
                "gps_accuracy": payload.accuracy_meters,
                "updated_at": now_iso,
            },
        )

        # Update pickup stop to COMPLETED
        await self.db.update_by_id(
            "delivery_stops",
            pickup_stop["id"],
            {"status": DeliveryStopStatus.COMPLETED.value, "completed_at": now_iso},
        )

        # Advance delivery state to PICKED_UP
        await self.db.update_by_id(
            "deliveries",
            delivery_id,
            {"status": DeliveryStatus.PICKED_UP.value, "picked_up_at": now_iso},
        )

        # Apply tamper-evident seal
        seal = await self.seal_service.create_pickup_seal(
            donation_id=delivery["donation_id"],
            delivery_id=delivery_id,
            applied_by_user_id=driver_user_id,
        )

        # Audit events
        await self.audit.log_event(
            action="PICKUP_VERIFIED",
            entity_type="deliveries",
            entity_id=delivery_id,
            user_id=driver_user_id,
            new_values={"handoff_id": handoff_rec["id"], "seal_id": seal.seal_id},
        )
        await self.audit.log_event(
            action="PACKAGE_SEALED",
            entity_type="package_seals",
            entity_id=seal.id,
            user_id=driver_user_id,
            new_values={"seal_id": seal.seal_id, "status": SealStatus.INTACT.value},
        )

        # Notifications
        donation = await self.db.get_by_id("donations", delivery["donation_id"], id_column="id")
        if donation and donation.get("donor_id"):
            await self.notification.notify_event(
                user_id=donation["donor_id"],
                event_type="PICKUP_VERIFIED",
                title="Pickup Verified",
                message=f"Food handoff verified and package sealed ({seal.seal_id}) for transit.",
                data={"delivery_id": delivery_id, "seal_id": seal.seal_id},
            )

        return DeliveryResponse(**(await self._get_delivery_with_stops(delivery_id)))

    # ─── PICKUP EVIDENCE ────────────────────────────────────────────────────

    async def record_pickup_evidence(
        self,
        delivery_id: str,
        driver_user_id: str,
        payload: PickupEvidenceRequest,
    ) -> List[HandoffEvidenceResponse]:
        """Driver uploads package and seal photos upon pickup."""
        delivery = await self._get_delivery_with_stops(delivery_id)
        driver_prof = await self.driver_service.get_driver_profile(driver_user_id)

        if delivery.get("driver_id") != driver_prof.id:
            raise ForbiddenException("You are not the assigned delivery partner.")

        pickup_stop = next((s for s in delivery["stops"] if s["stop_type"] == DeliveryStopType.PICKUP.value), None)
        stop_id = pickup_stop["id"] if pickup_stop else None

        now_iso = datetime.now(timezone.utc).isoformat()
        results: List[HandoffEvidenceResponse] = []

        # 1. Package photo
        pkg_id = str(uuid.uuid4())
        pkg_path = f"handoff-evidence/deliveries/{delivery_id}/pickup/package_{pkg_id[:8]}.jpg"
        pkg_rec = {
            "id": pkg_id,
            "delivery_id": delivery_id,
            "stop_id": stop_id,
            "evidence_type": EvidenceType.PACKAGE_PHOTO.value,
            "storage_path": pkg_path,
            "captured_by": driver_prof.id,
            "latitude": payload.latitude,
            "longitude": payload.longitude,
            "metadata": payload.metadata or {},
            "captured_at": now_iso,
        }
        res_pkg = await self.db.insert("handoff_evidence", pkg_rec)
        results.append(HandoffEvidenceResponse(**res_pkg))

        # 2. Seal photo
        seal_rec_id = str(uuid.uuid4())
        seal_path = f"handoff-evidence/deliveries/{delivery_id}/pickup/seal_{seal_rec_id[:8]}.jpg"
        seal_rec = {
            "id": seal_rec_id,
            "delivery_id": delivery_id,
            "stop_id": stop_id,
            "evidence_type": EvidenceType.SEAL_PHOTO.value,
            "storage_path": seal_path,
            "captured_by": driver_prof.id,
            "latitude": payload.latitude,
            "longitude": payload.longitude,
            "metadata": payload.metadata or {},
            "captured_at": now_iso,
        }
        res_seal = await self.db.insert("handoff_evidence", seal_rec)
        results.append(HandoffEvidenceResponse(**res_seal))

        await self.audit.log_event(
            action="PICKUP_EVIDENCE_UPLOADED",
            entity_type="deliveries",
            entity_id=delivery_id,
            user_id=driver_user_id,
            new_values={"evidence_count": 2},
        )

        return results

    # ─── DELIVERY OTP ───────────────────────────────────────────────────────

    async def generate_delivery_otp(
        self,
        delivery_id: str,
        stop_id: str,
        caller_user_id: str,
        caller_role: str,
    ) -> OTPGenerationResponse:
        """Generates single-use delivery verification OTP for the receiver to share with the driver."""
        delivery = await self._get_delivery_with_stops(delivery_id)
        stop = next((s for s in delivery["stops"] if s["id"] == stop_id), None)
        if not stop:
            raise NotFoundException("Delivery stop not found.")

        if stop["stop_type"] != DeliveryStopType.DELIVERY.value:
            raise ValidationException("OTP can only be generated for delivery stops.")

        # Check receiver authorization
        if caller_role != "ADMIN":
            receiver_prof = await self.db.get_by_id("receiver_profiles", caller_user_id, id_column="user_id")
            if not receiver_prof or stop.get("receiver_id") != receiver_prof["id"]:
                raise ForbiddenException("Only the designated receiver organization can generate this delivery OTP.")

        # Invalidate any older active pending OTP for this stop
        existing_otps = await self.db.query(
            "handoff_verifications",
            params={
                "delivery_id": f"eq.{delivery_id}",
                "stop_id": f"eq.{stop_id}",
                "handoff_type": f"eq.{HandoffType.DELIVERY.value}",
                "status": f"eq.{HandoffStatus.PENDING.value}",
            },
        )
        for old in existing_otps:
            await self.db.update_by_id("handoff_verifications", old["id"], {"status": HandoffStatus.EXPIRED.value})

        plaintext_otp, otp_hash, expires_at = self.otp_service.generate_otp()
        record_id = str(uuid.uuid4())
        now_iso = datetime.now(timezone.utc).isoformat()

        record = {
            "id": record_id,
            "delivery_id": delivery_id,
            "stop_id": stop_id,
            "handoff_type": HandoffType.DELIVERY.value,
            "otp_hash": otp_hash,
            "attempts": 0,
            "max_attempts": self.otp_service.max_attempts,
            "expires_at": expires_at.isoformat(),
            "status": HandoffStatus.PENDING.value,
            "created_at": now_iso,
            "updated_at": now_iso,
        }

        await self.db.insert("handoff_verifications", record)

        await self.audit.log_event(
            action="DELIVERY_OTP_ISSUED",
            entity_type="delivery_stops",
            entity_id=stop_id,
            user_id=caller_user_id,
            new_values={"handoff_id": record_id, "expires_at": expires_at.isoformat()},
        )

        return OTPGenerationResponse(
            delivery_id=delivery_id,
            stop_id=stop_id,
            handoff_type=HandoffType.DELIVERY,
            otp=plaintext_otp,
            expires_at=expires_at.isoformat(),
        )

    async def verify_delivery(
        self,
        delivery_id: str,
        stop_id: str,
        driver_user_id: str,
        payload: HandoffVerificationRequest,
        seal_condition: Optional[SealStatus] = None,
    ) -> DeliveryResponse:
        """Driver verifies delivery handoff at a stop with receiver-supplied OTP and GPS proximity."""
        delivery = await self._get_delivery_with_stops(delivery_id)
        driver_prof = await self.driver_service.get_driver_profile(driver_user_id)

        # 1. Driver assignment check
        if delivery.get("driver_id") != driver_prof.id:
            raise ForbiddenException("You are not the assigned delivery partner.")

        # 2. Stop check
        stop = next((s for s in delivery["stops"] if s["id"] == stop_id), None)
        if not stop:
            raise NotFoundException("Delivery stop not found.")
        if stop["stop_type"] != DeliveryStopType.DELIVERY.value:
            raise ValidationException("Target stop is not a delivery destination.")

        # 3. Delivery status must be AT_STOP (or IN_TRANSIT, auto-advancing to AT_STOP)
        if delivery.get("status") not in (DeliveryStatus.AT_STOP.value, DeliveryStatus.IN_TRANSIT.value):
            raise ConflictException(
                f"Delivery must be at destination stop (current: {delivery.get('status')}).",
                error_code="INVALID_DELIVERY_STATE",
            )

        # 4. GPS proximity check
        loc = await self.db.get_by_id("locations", stop["location_id"], id_column="id")
        if loc:
            s_lat = float(loc.get("latitude", 28.5672))
            s_lon = float(loc.get("longitude", 77.1982))
            dist = self.routing.calculate_distance(payload.latitude, payload.longitude, s_lat, s_lon)
            if dist > self.DELIVERY_PROXIMITY_RADIUS_KM:
                logger.warning("Driver GPS is %.2f km from delivery stop (limit: 0.3 km)", dist)
                raise ConflictException(
                    f"Driver is outside the delivery stop proximity radius ({int(dist * 1000)}m > 300m).",
                    error_code="PROXIMITY_CHECK_FAILED",
                )

        # 5. Fetch active pending OTP
        otps = await self.db.query(
            "handoff_verifications",
            params={
                "delivery_id": f"eq.{delivery_id}",
                "stop_id": f"eq.{stop_id}",
                "handoff_type": f"eq.{HandoffType.DELIVERY.value}",
                "status": f"eq.{HandoffStatus.PENDING.value}",
            },
            order="created_at.desc",
            limit=1,
        )
        if not otps:
            raise ConflictException("Invalid or expired verification code.", error_code="OTP_VERIFICATION_FAILED")

        handoff_rec = otps[0]
        verif_result = self.otp_service.verify_otp(
            candidate_otp=payload.otp,
            stored_hash=handoff_rec["otp_hash"],
            expires_at_iso=handoff_rec["expires_at"],
            current_attempts=int(handoff_rec.get("attempts", 0)),
        )

        now_iso = datetime.now(timezone.utc).isoformat()

        if not verif_result["is_valid"]:
            upd = {"attempts": verif_result["new_attempts"], "updated_at": now_iso}
            if verif_result["attempts_exceeded"] or verif_result["is_expired"]:
                upd["status"] = HandoffStatus.FAILED.value if verif_result["attempts_exceeded"] else HandoffStatus.EXPIRED.value

            await self.db.update_by_id("handoff_verifications", handoff_rec["id"], upd)
            await self.audit.log_event(
                action="DELIVERY_OTP_FAILED",
                entity_type="handoff_verifications",
                entity_id=handoff_rec["id"],
                user_id=driver_user_id,
                new_values={"attempts": verif_result["new_attempts"]},
            )
            raise ConflictException("Invalid or expired verification code.", error_code="OTP_VERIFICATION_FAILED")

        # Success: Mark handoff verified
        await self.db.update_by_id(
            "handoff_verifications",
            handoff_rec["id"],
            {
                "status": HandoffStatus.VERIFIED.value,
                "verified_by": driver_prof.id,
                "verified_at": now_iso,
                "latitude": payload.latitude,
                "longitude": payload.longitude,
                "gps_accuracy": payload.accuracy_meters,
                "updated_at": now_iso,
            },
        )

        # Mark this delivery stop as COMPLETED
        await self.db.update_by_id(
            "delivery_stops",
            stop_id,
            {"status": DeliveryStopStatus.COMPLETED.value, "completed_at": now_iso},
        )

        # Record seal condition
        observed_seal = seal_condition or SealStatus.INTACT
        await self.seal_service.record_delivery_seal(delivery_id, observed_seal)

        if observed_seal in (SealStatus.BROKEN, SealStatus.MISSING, SealStatus.DISPUTED):
            await self.audit.log_event(
                action="SEAL_DISCREPANCY_DETECTED",
                entity_type="deliveries",
                entity_id=delivery_id,
                user_id=driver_user_id,
                new_values={"seal_status": observed_seal.value, "stop_id": stop_id},
            )
            # Notify of discrepancy
            donation = await self.db.get_by_id("donations", delivery["donation_id"], id_column="id")
            if donation and donation.get("donor_id"):
                await self.notification.notify_event(
                    user_id=donation["donor_id"],
                    event_type="SEAL_DISCREPANCY",
                    title="Package Seal Discrepancy",
                    message="Seal discrepancy detected — manual review required.",
                    data={"delivery_id": delivery_id, "seal_status": observed_seal.value},
                )

        await self.audit.log_event(
            action="DELIVERY_VERIFIED",
            entity_type="delivery_stops",
            entity_id=stop_id,
            user_id=driver_user_id,
            new_values={"handoff_id": handoff_rec["id"], "seal_status": observed_seal.value},
        )

        # Check remaining delivery stops
        refreshed_delivery = await self._get_delivery_with_stops(delivery_id)
        delivery_stops = [s for s in refreshed_delivery["stops"] if s["stop_type"] == DeliveryStopType.DELIVERY.value]
        all_completed = all(s["status"] == DeliveryStopStatus.COMPLETED.value for s in delivery_stops)

        if all_completed:
            # Full mission completed -> DELIVERED
            await self.db.update_by_id(
                "deliveries",
                delivery_id,
                {"status": DeliveryStatus.DELIVERED.value, "completed_at": now_iso},
            )
            # Free driver
            await self.db.update_by_id(
                "driver_profiles",
                driver_prof.id,
                {"availability_status": DriverAvailabilityStatus.AVAILABLE.value},
            )
            donation = await self.db.get_by_id("donations", delivery["donation_id"], id_column="id")
            if donation and donation.get("donor_id"):
                await self.notification.notify_event(
                    user_id=donation["donor_id"],
                    event_type="DELIVERY_COMPLETED",
                    title="Food Rescue Completed",
                    message="All delivery stops verified and completed successfully!",
                    data={"delivery_id": delivery_id},
                )
        else:
            # More stops remain -> IN_TRANSIT to next
            await self.db.update_by_id(
                "deliveries",
                delivery_id,
                {"status": DeliveryStatus.IN_TRANSIT.value},
            )

        return DeliveryResponse(**(await self._get_delivery_with_stops(delivery_id)))

    # ─── DELIVERY EVIDENCE ──────────────────────────────────────────────────

    async def record_delivery_evidence(
        self,
        delivery_id: str,
        stop_id: str,
        driver_user_id: str,
        payload: DeliveryEvidenceRequest,
    ) -> List[HandoffEvidenceResponse]:
        """Driver uploads package and seal photos upon arrival at delivery stop."""
        delivery = await self._get_delivery_with_stops(delivery_id)
        driver_prof = await self.driver_service.get_driver_profile(driver_user_id)

        if delivery.get("driver_id") != driver_prof.id:
            raise ForbiddenException("You are not the assigned delivery partner.")

        now_iso = datetime.now(timezone.utc).isoformat()
        results: List[HandoffEvidenceResponse] = []

        # 1. Package photo
        pkg_id = str(uuid.uuid4())
        pkg_path = f"handoff-evidence/deliveries/{delivery_id}/stops/{stop_id}/delivery/package_{pkg_id[:8]}.jpg"
        pkg_rec = {
            "id": pkg_id,
            "delivery_id": delivery_id,
            "stop_id": stop_id,
            "evidence_type": EvidenceType.PACKAGE_PHOTO.value,
            "storage_path": pkg_path,
            "captured_by": driver_prof.id,
            "latitude": payload.latitude,
            "longitude": payload.longitude,
            "metadata": payload.metadata or {},
            "captured_at": now_iso,
        }
        res_pkg = await self.db.insert("handoff_evidence", pkg_rec)
        results.append(HandoffEvidenceResponse(**res_pkg))

        # 2. Seal photo
        seal_id = str(uuid.uuid4())
        seal_path = f"handoff-evidence/deliveries/{delivery_id}/stops/{stop_id}/delivery/seal_{seal_id[:8]}.jpg"
        seal_rec = {
            "id": seal_id,
            "delivery_id": delivery_id,
            "stop_id": stop_id,
            "evidence_type": EvidenceType.SEAL_PHOTO.value,
            "storage_path": seal_path,
            "captured_by": driver_prof.id,
            "latitude": payload.latitude,
            "longitude": payload.longitude,
            "metadata": payload.metadata or {},
            "captured_at": now_iso,
        }
        res_seal = await self.db.insert("handoff_evidence", seal_rec)
        results.append(HandoffEvidenceResponse(**res_seal))

        await self.audit.log_event(
            action="DELIVERY_EVIDENCE_UPLOADED",
            entity_type="delivery_stops",
            entity_id=stop_id,
            user_id=driver_user_id,
            new_values={"evidence_count": 2},
        )

        # Trigger food integrity check if pickup photo exists
        pickup_evidences = await self.db.query(
            "handoff_evidence",
            params={
                "delivery_id": f"eq.{delivery_id}",
                "evidence_type": f"eq.{EvidenceType.PACKAGE_PHOTO.value}",
            },
        )
        pickup_pkg = next((e for e in pickup_evidences if not e.get("stop_id") or "pickup" in e.get("storage_path", "")), None)

        if pickup_pkg:
            seal_info = await self.seal_service.get_seal_by_delivery(delivery_id)
            await self.integrity_service.perform_integrity_check(
                delivery_id=delivery_id,
                stop_id=stop_id,
                pickup_image_path=pickup_pkg["storage_path"],
                delivery_image_path=pkg_path,
                seal_id=seal_info.seal_id if seal_info else None,
                pickup_seal_status=seal_info.pickup_status.value if seal_info else "INTACT",
                delivery_seal_status=payload.seal_condition.value,
            )

        return results

    async def get_evidence(
        self,
        delivery_id: str,
        user_id: str,
        user_role: str,
    ) -> List[HandoffEvidenceResponse]:
        """Fetches private handoff evidence for authorized participants."""
        delivery = await self._get_delivery_with_stops(delivery_id)

        # Authorization: Admin, assigned Driver, Donor of donation, or Receiver of any stop
        if user_role == "ADMIN":
            pass
        elif user_role == "DRIVER":
            driver_prof = await self.db.get_by_id("driver_profiles", user_id, id_column="user_id")
            if not driver_prof or delivery.get("driver_id") != driver_prof["id"]:
                raise ForbiddenException("Unauthorized to view delivery evidence.")
        elif user_role == "DONOR":
            donation = await self.db.get_by_id("donations", delivery["donation_id"], id_column="id")
            if not donation or donation.get("donor_id") != user_id:
                raise ForbiddenException("Unauthorized to view donation evidence.")
        elif user_role == "RECEIVER":
            receiver_prof = await self.db.get_by_id("receiver_profiles", user_id, id_column="user_id")
            receiver_stops = [s for s in delivery["stops"] if s.get("receiver_id") == (receiver_prof["id"] if receiver_prof else None)]
            if not receiver_stops:
                raise ForbiddenException("Unauthorized to view delivery evidence.")
        else:
            raise ForbiddenException("Unauthorized.")

        records = await self.db.query("handoff_evidence", params={"delivery_id": f"eq.{delivery_id}"})
        return [HandoffEvidenceResponse(**r) for r in records]
