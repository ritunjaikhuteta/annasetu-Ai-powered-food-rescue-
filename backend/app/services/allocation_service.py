"""Donation Allocation Service with Concurrency Protection."""

import asyncio
from collections import defaultdict
import logging
from typing import Dict, Optional
import uuid
from app.db.supabase import SupabaseClient
from app.schemas.allocation import AllocationCreate, AllocationResponse, AllocationStatus
from app.schemas.donation import DonationStatus
from app.schemas.need import NeedStatus
from app.services.audit_service import AuditService
from app.utils.exceptions import ConflictException, ForbiddenException, NotFoundException, ValidationException

logger = logging.getLogger("annasetu.services.allocation")

# In-process lock dictionary to serialize allocations on the same donation
_donation_locks: Dict[str, asyncio.Lock] = defaultdict(asyncio.Lock)


class AllocationService:
    """Service managing atomic food rescue allocations and race condition prevention."""

    def __init__(self, db: SupabaseClient):
        self.db = db
        self.audit = AuditService(db)

    async def create_allocation(
        self,
        payload: AllocationCreate,
        user_id: str,
        user_role: str,
    ) -> AllocationResponse:
        """Atomically allocates a portion of a donation to an NGO need.

        Enforces transactional consistency and CAS optimistic locking to eliminate over-allocation.
        """
        qty = payload.allocated_quantity_kg
        if qty <= 0:
            raise ValidationException("Allocated quantity must be strictly greater than 0 kg.")

        donation_id = payload.donation_id
        need_id = payload.need_id

        # Concurrency barrier: serialize concurrent requests targeting the same donation
        lock = _donation_locks[donation_id]
        async with lock:
            # 1. Fetch donation and verify status
            donation = await self.db.get_by_id("donations", donation_id, id_column="id")
            if not donation:
                raise NotFoundException("Donation not found.", error_code="DONATION_NOT_FOUND")

            if donation.get("status") not in ("POSTED", "MATCHING", "MATCHED", "ALLOCATED"):
                raise ValidationException(
                    f"Donation in '{donation.get('status')}' status cannot receive new allocations.",
                    error_code="DONATION_INACTIVE",
                )

            current_donation_rem = float(donation.get("remaining_quantity_kg", 0.0))
            if qty > current_donation_rem:
                raise ConflictException(
                    f"Allocation request of {qty} kg exceeds remaining donation quantity of {current_donation_rem} kg.",
                    error_code="QUANTITY_EXCEEDED",
                )

            # 2. Fetch need and verify status
            need = await self.db.get_by_id("ngo_needs", need_id, id_column="id")
            if not need:
                raise NotFoundException("Target NGO Need not found.", error_code="NEED_NOT_FOUND")

            if need.get("status") not in (NeedStatus.ACTIVE.value, NeedStatus.PARTIALLY_FULFILLED.value):
                raise ValidationException(
                    f"Need in '{need.get('status')}' status is not active for allocation.",
                    error_code="NEED_INACTIVE",
                )

            current_need_rem = float(need.get("remaining_quantity_kg", 0.0))
            if qty > current_need_rem:
                raise ConflictException(
                    f"Allocation request of {qty} kg exceeds remaining need requirement of {current_need_rem} kg.",
                    error_code="NEED_CAPACITY_EXCEEDED",
                )

            # 3. If match_id provided, verify match validity
            if payload.match_id:
                match_rec = await self.db.get_by_id("matches", payload.match_id, id_column="id")
                if not match_rec:
                    raise NotFoundException("Associated match record not found.", error_code="MATCH_NOT_FOUND")
                if match_rec.get("status") not in ("PROPOSED", "ACCEPTED"):
                    raise ValidationException("Associated match is no longer valid.")

            # 4. Atomic CAS update on donation remaining quantity
            new_donation_rem = round(current_donation_rem - qty, 2)
            new_donation_status = (
                DonationStatus.ALLOCATED.value if new_donation_rem == 0.0 else DonationStatus.MATCHED.value
            )

            cas_donation = await self.db.compare_and_swap_update(
                table="donations",
                id_value=donation_id,
                expected_field="remaining_quantity_kg",
                expected_val=current_donation_rem,
                new_values={
                    "remaining_quantity_kg": new_donation_rem,
                    "status": new_donation_status,
                },
            )

            if not cas_donation:
                # Concurrent update took place between fetch and CAS
                raise ConflictException(
                    "Concurrent modification detected on donation quantity. Please retry.",
                    error_code="CONCURRENT_UPDATE_CONFLICT",
                )

            # 5. Atomic CAS update on need remaining quantity
            new_need_rem = round(current_need_rem - qty, 2)
            new_need_status = (
                NeedStatus.FULFILLED.value if new_need_rem == 0.0 else NeedStatus.PARTIALLY_FULFILLED.value
            )

            cas_need = await self.db.compare_and_swap_update(
                table="ngo_needs",
                id_value=need_id,
                expected_field="remaining_quantity_kg",
                expected_val=current_need_rem,
                new_values={
                    "remaining_quantity_kg": new_need_rem,
                    "status": new_need_status,
                },
            )

            if not cas_need:
                # Rollback donation quantity change to maintain invariant integrity
                await self.db.update_by_id(
                    "donations",
                    donation_id,
                    {"remaining_quantity_kg": current_donation_rem, "status": donation.get("status")},
                )
                raise ConflictException(
                    "Concurrent modification detected on need requirement. Allocation rolled back.",
                    error_code="CONCURRENT_NEED_CONFLICT",
                )

            # 6. Insert donation allocation record
            allocation_id = str(uuid.uuid4())
            allocation_record = {
                "id": allocation_id,
                "donation_id": donation_id,
                "need_id": need_id,
                "match_id": payload.match_id,
                "allocated_quantity_kg": qty,
                "status": AllocationStatus.RESERVED.value,
            }

            created = await self.db.insert("donation_allocations", allocation_record)

            # 7. Update match status to ACCEPTED if applicable
            if payload.match_id:
                await self.db.update_by_id("matches", payload.match_id, {"status": "ACCEPTED"})

            # 8. Record audit log
            await self.audit.log_event(
                action="ALLOCATION_CREATED",
                entity_type="donation_allocations",
                entity_id=allocation_id,
                user_id=user_id,
                new_values={
                    "donation_id": donation_id,
                    "need_id": need_id,
                    "allocated_quantity_kg": qty,
                    "new_donation_remaining_kg": new_donation_rem,
                    "new_need_remaining_kg": new_need_rem,
                },
            )

            logger.info(
                "Allocated %.1f kg from donation %s (left: %.1f kg) to need %s (left: %.1f kg)",
                qty,
                donation_id,
                new_donation_rem,
                need_id,
                new_need_rem,
            )

            return AllocationResponse(**created)
