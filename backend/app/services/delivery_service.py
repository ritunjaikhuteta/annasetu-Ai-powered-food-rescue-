"""Delivery Domain Service."""

import asyncio
from collections import defaultdict
from datetime import datetime, timedelta, timezone
import logging
from typing import Any, Dict, List, Optional
import uuid
from app.db.supabase import SupabaseClient
from app.schemas.delivery import (
    DeliveryCreate,
    DeliveryResponse,
    DeliveryStatus,
    DeliveryStopResponse,
    DeliveryStopStatus,
    DeliveryStopType,
    ProximityCheckRequest,
)
from app.schemas.delivery_offer import DeliveryOfferResponse, DeliveryOfferStatus
from app.schemas.driver import DriverAvailabilityStatus, EligibleDriverResponse
from app.services.audit_service import AuditService
from app.services.driver_service import DriverService
from app.services.notification_service import NotificationService
from app.services.routing_provider import RoutingProvider, get_routing_provider
from app.services.routing_service import RoutingService
from app.utils.exceptions import ConflictException, ForbiddenException, NotFoundException, ValidationException

logger = logging.getLogger("annasetu.services.delivery")

# Concurrency mutex per delivery for acceptance synchronization
_delivery_locks: Dict[str, asyncio.Lock] = defaultdict(asyncio.Lock)


class DeliveryService:
    """Core logistics and delivery service managing multi-stop missions, driver offers, and state transitions."""

    # Proximity thresholds in kilometers (Section 15)
    PICKUP_PROXIMITY_RADIUS_KM = 0.30  # 300 meters
    STOP_PROXIMITY_RADIUS_KM = 0.30    # 300 meters

    # Allowed forward state machine transitions (Section 13)
    VALID_TRANSITIONS: Dict[str, List[str]] = {
        DeliveryStatus.OPEN.value: [DeliveryStatus.ACCEPTED.value, DeliveryStatus.CANCELLED.value],
        DeliveryStatus.ACCEPTED.value: [
            DeliveryStatus.ARRIVING_PICKUP.value,
            DeliveryStatus.REASSIGNMENT_REQUIRED.value,
            DeliveryStatus.CANCELLED.value,
        ],
        DeliveryStatus.ARRIVING_PICKUP.value: [
            DeliveryStatus.PICKED_UP.value,
            DeliveryStatus.FAILED_PICKUP.value,
            DeliveryStatus.REASSIGNMENT_REQUIRED.value,
        ],
        DeliveryStatus.PICKED_UP.value: [DeliveryStatus.IN_TRANSIT.value],
        DeliveryStatus.IN_TRANSIT.value: [
            DeliveryStatus.AT_STOP.value,
            DeliveryStatus.FAILED_DELIVERY.value,
        ],
        DeliveryStatus.AT_STOP.value: [
            DeliveryStatus.IN_TRANSIT.value,  # More stops remaining
            DeliveryStatus.DELIVERED.value,    # All stops completed
            DeliveryStatus.FAILED_DELIVERY.value,
        ],
        DeliveryStatus.REASSIGNMENT_REQUIRED.value: [
            DeliveryStatus.OPEN.value,
            DeliveryStatus.CANCELLED.value,
        ],
    }

    def __init__(
        self,
        db: SupabaseClient,
        routing: Optional[RoutingProvider] = None,
    ):
        self.db = db
        self.routing = routing or get_routing_provider()
        self.routing_service = RoutingService(self.routing)
        self.driver_service = DriverService(db, self.routing)
        self.notification = NotificationService(db)
        self.audit = AuditService(db)

    @staticmethod
    def _parse_iso(timestamp_str: str) -> datetime:
        clean = timestamp_str.replace("Z", "+00:00")
        dt = datetime.fromisoformat(clean)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt

    async def create_delivery(
        self,
        payload: DeliveryCreate,
        creator_id: str,
        creator_role: str,
    ) -> DeliveryResponse:
        """Creates a delivery mission from accepted or reserved donation allocations."""
        donation = await self.db.get_by_id("donations", payload.donation_id, id_column="id")
        if not donation:
            raise NotFoundException("Donation not found.", error_code="DONATION_NOT_FOUND")

        if donation.get("status") in ("CANCELLED", "EXPIRED"):
            raise ValidationException("Cannot create delivery for cancelled or expired donation.")

        # Verify donor pickup location
        pickup_loc = await self.db.get_by_id("locations", donation["pickup_location_id"], id_column="id")
        if not pickup_loc:
            raise NotFoundException("Pickup location record not found.", error_code="LOCATION_NOT_FOUND")

        p_lat = float(pickup_loc.get("latitude", 28.6139))
        p_lon = float(pickup_loc.get("longitude", 77.2090))

        # Validate allocations (max 3 stops for MVP)
        if len(payload.allocation_ids) > 3:
            raise ValidationException("A delivery mission supports a maximum of 3 allocation stops.")

        allocations_info = []
        total_kg = 0.0

        for alloc_id in payload.allocation_ids:
            alloc = await self.db.get_by_id("donation_allocations", alloc_id, id_column="id")
            if not alloc:
                raise NotFoundException(f"Allocation {alloc_id} not found.", error_code="ALLOCATION_NOT_FOUND")

            if alloc.get("donation_id") != payload.donation_id:
                raise ValidationException(f"Allocation {alloc_id} does not belong to donation {payload.donation_id}.")

            if alloc.get("status") not in ("RESERVED", "ACCEPTED"):
                raise ConflictException(f"Allocation {alloc_id} is in invalid status '{alloc.get('status')}'.")

            qty = float(alloc.get("allocated_quantity_kg", 0.0))
            if qty <= 0:
                raise ValidationException(f"Allocation {alloc_id} has invalid quantity.")
            total_kg += qty

            need = await self.db.get_by_id("ngo_needs", alloc["need_id"], id_column="id")
            if not need:
                raise NotFoundException("Target need for allocation not found.")

            need_loc = await self.db.get_by_id("locations", need["location_id"], id_column="id")
            if not need_loc:
                raise NotFoundException(f"Receiving center location for need {need['id']} not found.")

            allocations_info.append({
                "allocation_id": alloc_id,
                "receiver_id": need["receiver_id"],
                "location_id": need["location_id"],
                "latitude": float(need_loc.get("latitude", 28.6139)),
                "longitude": float(need_loc.get("longitude", 77.2090)),
                "quantity_kg": qty,
                "required_by": need["required_by"],
            })

        # Evaluate deterministic multi-stop route
        start_time = datetime.now(timezone.utc)
        rescue_deadline = self._parse_iso(donation["rescue_deadline"])

        route_eval = self.routing_service.evaluate_multistop_route(
            pickup_lat=p_lat,
            pickup_lon=p_lon,
            stops_info=allocations_info,
            start_time=start_time,
            rescue_deadline=rescue_deadline,
        )

        delivery_id = str(uuid.uuid4())
        # Pick default vehicle class based on total payload weight
        v_class = "auto" if total_kg <= 75 else ("van" if total_kg <= 500 else "truck")

        delivery_record = {
            "id": delivery_id,
            "donation_id": payload.donation_id,
            "vehicle_type": v_class,
            "total_quantity_kg": round(total_kg, 2),
            "total_distance_km": route_eval["total_distance_km"],
            "estimated_duration_minutes": route_eval["estimated_duration_minutes"],
            "status": DeliveryStatus.OPEN.value,
        }

        created_delivery = await self.db.insert("deliveries", delivery_record)

        # Insert Stop 1: Pickup
        stops_created = []
        pickup_stop_payload = {
            "id": str(uuid.uuid4()),
            "delivery_id": delivery_id,
            "sequence_number": 1,
            "stop_type": DeliveryStopType.PICKUP.value,
            "location_id": donation["pickup_location_id"],
            "quantity_kg": total_kg,
            "distance_from_prev_km": 0.0,
            "estimated_arrival": start_time.isoformat(),
            "status": DeliveryStopStatus.PENDING.value,
        }
        stops_created.append(await self.db.insert("delivery_stops", pickup_stop_payload))

        # Insert Delivery Stops
        for stop_data in route_eval["ordered_stops"]:
            stop_payload = {
                "id": str(uuid.uuid4()),
                "delivery_id": delivery_id,
                "sequence_number": stop_data["sequence_number"],
                "stop_type": DeliveryStopType.DELIVERY.value,
                "location_id": stop_data["location_id"],
                "receiver_id": stop_data.get("receiver_id"),
                "allocation_id": stop_data.get("allocation_id"),
                "quantity_kg": stop_data["quantity_kg"],
                "distance_from_prev_km": stop_data["distance_from_prev_km"],
                "estimated_arrival": stop_data["estimated_arrival"],
                "status": DeliveryStopStatus.PENDING.value,
            }
            stops_created.append(await self.db.insert("delivery_stops", stop_payload))

        await self.audit.log_event(
            action="DELIVERY_CREATED",
            entity_type="deliveries",
            entity_id=delivery_id,
            user_id=creator_id,
            new_values={
                "total_quantity_kg": total_kg,
                "stops_count": len(stops_created),
            },
        )

        return DeliveryResponse(
            **created_delivery,
            stops=[DeliveryStopResponse(**s) for s in stops_created],
        )

    async def get_delivery(self, delivery_id: str) -> DeliveryResponse:
        """Retrieves full delivery record with ordered stops."""
        delivery = await self.db.get_by_id("deliveries", delivery_id, id_column="id")
        if not delivery:
            raise NotFoundException("Delivery mission not found.", error_code="DELIVERY_NOT_FOUND")

        stops_records = await self.db.query(
            "delivery_stops",
            params={"delivery_id": f"eq.{delivery_id}"},
            order="sequence_number.asc",
        )

        return DeliveryResponse(
            **delivery,
            stops=[DeliveryStopResponse(**s) for s in stops_records],
        )

    async def get_eligible_drivers(self, delivery_id: str) -> List[EligibleDriverResponse]:
        """Finds eligible verified drivers within radius for a delivery."""
        delivery = await self.db.get_by_id("deliveries", delivery_id, id_column="id")
        if not delivery:
            raise NotFoundException("Delivery not found.", error_code="DELIVERY_NOT_FOUND")

        # Get pickup stop location
        stops = await self.db.query(
            "delivery_stops",
            params={"delivery_id": f"eq.{delivery_id}", "stop_type": "eq.PICKUP"},
        )
        if not stops:
            raise ValidationException("Pickup stop missing for delivery.")

        loc = await self.db.get_by_id("locations", stops[0]["location_id"], id_column="id")
        p_lat = float(loc.get("latitude", 28.6139))
        p_lon = float(loc.get("longitude", 77.2090))

        donation = await self.db.get_by_id("donations", delivery["donation_id"], id_column="id")
        pickup_deadline = self._parse_iso(donation["rescue_deadline"]) if donation else datetime.now(timezone.utc) + timedelta(hours=4)

        return await self.driver_service.find_eligible_drivers(
            delivery_quantity_kg=float(delivery["total_quantity_kg"]),
            pickup_lat=p_lat,
            pickup_lon=p_lon,
            pickup_deadline=pickup_deadline,
        )

    async def create_offers(
        self,
        delivery_id: str,
        driver_ids: Optional[List[str]] = None,
    ) -> List[DeliveryOfferResponse]:
        """Dispatches delivery offers to eligible drivers."""
        delivery = await self.db.get_by_id("deliveries", delivery_id, id_column="id")
        if not delivery:
            raise NotFoundException("Delivery not found.")

        if delivery.get("status") not in (DeliveryStatus.OPEN.value, DeliveryStatus.REASSIGNMENT_REQUIRED.value):
            raise ConflictException(f"Cannot dispatch offers for delivery in status '{delivery.get('status')}'.")

        target_driver_ids = driver_ids
        if not target_driver_ids:
            eligible_drivers = await self.get_eligible_drivers(delivery_id)
            target_driver_ids = [d.id for d in eligible_drivers]

        if not target_driver_ids:
            return []

        dist = float(delivery.get("total_distance_km", 10.0))
        dur = int(delivery.get("estimated_duration_minutes", 30))
        # Deterministic base charge: ₹100 base + ₹15/km
        charge = round(100.0 + (dist * 15.0), 2)
        payout = round(charge * 0.85, 2)  # 85% to driver partner
        expires_at = (datetime.now(timezone.utc) + timedelta(minutes=15)).isoformat()

        offers_created = []
        for d_id in target_driver_ids:
            # Check existing active offer
            existing = await self.db.query(
                "delivery_offers",
                params={"delivery_id": f"eq.{delivery_id}", "driver_id": f"eq.{d_id}", "status": "eq.OFFERED"},
            )
            if existing:
                offers_created.append(DeliveryOfferResponse(**existing[0]))
                continue

            offer_id = str(uuid.uuid4())
            offer_payload = {
                "id": offer_id,
                "delivery_id": delivery_id,
                "driver_id": d_id,
                "vehicle_type": delivery.get("vehicle_type", "auto"),
                "offered_delivery_charge": charge,
                "estimated_driver_payout": payout,
                "estimated_distance_km": dist,
                "estimated_duration_minutes": dur,
                "expires_at": expires_at,
                "status": DeliveryOfferStatus.OFFERED.value,
            }
            res = await self.db.insert("delivery_offers", offer_payload)
            offers_created.append(DeliveryOfferResponse(**res))

            # Fetch driver profile to notify
            driver_prof = await self.db.get_by_id("driver_profiles", d_id, id_column="id")
            if driver_prof:
                await self.notification.notify_receiver_match(
                    receiver_user_id=driver_prof["user_id"],
                    match_id=offer_id,
                    donation_id=delivery["donation_id"],
                    fulfillable_quantity_kg=float(delivery["total_quantity_kg"]),
                    diet_type="SURPLUS",
                    priority_label="HIGH",
                )

        await self.audit.log_event("DRIVER_OFFER_CREATED", "deliveries", delivery_id, new_values={"offers_count": len(offers_created)})
        return offers_created

    async def view_offer(self, offer_id: str, driver_user_id: str) -> DeliveryOfferResponse:
        offer = await self.db.get_by_id("delivery_offers", offer_id, id_column="id")
        if not offer:
            raise NotFoundException("Offer not found.")

        if offer.get("status") == DeliveryOfferStatus.OFFERED.value:
            updated = await self.db.update_by_id("delivery_offers", offer_id, {"status": DeliveryOfferStatus.VIEWED.value})
            return DeliveryOfferResponse(**updated)
        return DeliveryOfferResponse(**offer)

    async def accept_offer(self, offer_id: str, driver_user_id: str) -> DeliveryResponse:
        """Atomically accepts an offer. Exactly one driver can win."""
        offer = await self.db.get_by_id("delivery_offers", offer_id, id_column="id")
        if not offer:
            raise NotFoundException("Offer not found.")

        if offer.get("status") not in (DeliveryOfferStatus.OFFERED.value, DeliveryOfferStatus.VIEWED.value):
            raise ConflictException(
                "Delivery offer is no longer active. Another partner may have already accepted.",
                error_code="DELIVERY_TAKEN",
            )

        delivery_id = offer["delivery_id"]
        driver_prof = await self.driver_service.get_driver_profile(driver_user_id)

        # Mutex lock per delivery
        lock = _delivery_locks[delivery_id]
        async with lock:
            delivery = await self.db.get_by_id("deliveries", delivery_id, id_column="id")
            if not delivery:
                raise NotFoundException("Delivery not found.")

            if delivery.get("status") not in (DeliveryStatus.OPEN.value, DeliveryStatus.REASSIGNMENT_REQUIRED.value):
                raise ConflictException("Delivery is no longer available. Another partner has already accepted.", error_code="DELIVERY_TAKEN")

            # Check driver availability
            if driver_prof.availability_status != DriverAvailabilityStatus.AVAILABLE:
                raise ConflictException("You are currently on another mission or offline.", error_code="DRIVER_BUSY")

            now_iso = datetime.now(timezone.utc).isoformat()

            # CAS update on delivery: assign driver and transition to ACCEPTED
            cas_res = await self.db.compare_and_swap_update(
                table="deliveries",
                id_value=delivery_id,
                expected_field="status",
                expected_val=delivery.get("status"),
                new_values={
                    "driver_id": driver_prof.id,
                    "status": DeliveryStatus.ACCEPTED.value,
                    "accepted_at": now_iso,
                },
            )

            if not cas_res:
                raise ConflictException("Delivery is no longer available.", error_code="DELIVERY_TAKEN")

            # 1. Update this offer to ACCEPTED
            await self.db.update_by_id("delivery_offers", offer_id, {"status": DeliveryOfferStatus.ACCEPTED.value})

            # 2. Cancel all other active offers for this delivery
            all_offers = await self.db.query("delivery_offers", params={"delivery_id": f"eq.{delivery_id}"})
            for o in all_offers:
                if o["id"] != offer_id and o.get("status") in (DeliveryOfferStatus.OFFERED.value, DeliveryOfferStatus.VIEWED.value):
                    await self.db.update_by_id("delivery_offers", o["id"], {"status": DeliveryOfferStatus.CANCELLED.value})

            # 3. Update driver status to ON_JOB
            await self.db.update_by_id("driver_profiles", driver_prof.id, {"availability_status": DriverAvailabilityStatus.ON_JOB.value})

            # 4. Audit log
            await self.audit.log_event(
                action="DRIVER_ASSIGNED",
                entity_type="deliveries",
                entity_id=delivery_id,
                user_id=driver_user_id,
                new_values={"driver_id": driver_prof.id, "accepted_at": now_iso},
            )

            # 5. Notifications
            donation = await self.db.get_by_id("donations", delivery["donation_id"], id_column="id")
            if donation and donation.get("donor_id"):
                await self.notification.notify_event(
                    user_id=donation["donor_id"],
                    event_type="DRIVER_ASSIGNED",
                    title="Driver Assigned",
                    message="A verified delivery partner has been assigned to your food rescue.",
                    data={"delivery_id": delivery_id, "event_key": "DRIVER_ASSIGNED"},
                )

            return await self.get_delivery(delivery_id)

    async def decline_offer(self, offer_id: str, driver_user_id: str) -> DeliveryOfferResponse:
        offer = await self.db.get_by_id("delivery_offers", offer_id, id_column="id")
        if not offer:
            raise NotFoundException("Offer not found.")

        updated = await self.db.update_by_id("delivery_offers", offer_id, {"status": DeliveryOfferStatus.DECLINED.value})
        await self.audit.log_event("DRIVER_OFFER_DECLINED", "delivery_offers", offer_id, user_id=driver_user_id)
        return DeliveryOfferResponse(**updated)

    async def cancel_delivery(self, delivery_id: str, user_id: str, user_role: str) -> DeliveryResponse:
        """Handles cancellation. If cancelled by driver, triggers REASSIGNMENT_REQUIRED."""
        delivery = await self.get_delivery(delivery_id)

        if delivery.status in (DeliveryStatus.DELIVERED, DeliveryStatus.CANCELLED):
            raise ConflictException(f"Cannot cancel delivery in status '{delivery.status.value}'.")

        if user_role == "DRIVER":
            # Assigned driver cancelling -> triggers reassignment flow
            if delivery.driver_id:
                await self.db.update_by_id(
                    "driver_profiles",
                    delivery.driver_id,
                    {"availability_status": DriverAvailabilityStatus.AVAILABLE.value},
                )

            updated = await self.db.update_by_id(
                "deliveries",
                delivery_id,
                {"status": DeliveryStatus.REASSIGNMENT_REQUIRED.value, "driver_id": None},
            )
            await self.audit.log_event(
                action="DRIVER_CANCELLED",
                entity_type="deliveries",
                entity_id=delivery_id,
                user_id=user_id,
                new_values={"status": DeliveryStatus.REASSIGNMENT_REQUIRED.value},
            )
            donation = await self.db.get_by_id("donations", delivery.donation_id, id_column="id")
            if donation and donation.get("donor_id"):
                await self.notification.notify_event(
                    user_id=donation["donor_id"],
                    event_type="REASSIGNMENT_REQUIRED",
                    title="Driver Cancelled Delivery",
                    message="The assigned driver partner cancelled the mission. Auto-reassignment initiated.",
                    data={"delivery_id": delivery_id, "event_key": "DRIVER_CANCELLED"},
                )
            return await self.get_delivery(delivery_id)
        else:
            # Donor or Admin cancellation
            if delivery.driver_id:
                await self.db.update_by_id(
                    "driver_profiles",
                    delivery.driver_id,
                    {"availability_status": DriverAvailabilityStatus.AVAILABLE.value},
                )
            updated = await self.db.update_by_id("deliveries", delivery_id, {"status": DeliveryStatus.CANCELLED.value})
            await self.audit.log_event("DELIVERY_CANCELLED", "deliveries", delivery_id, user_id=user_id)
            return await self.get_delivery(delivery_id)

    async def update_delivery_status(
        self,
        delivery_id: str,
        target_status: DeliveryStatus,
        driver_user_id: str,
        proximity: Optional[ProximityCheckRequest] = None,
        stop_id: Optional[str] = None,
    ) -> DeliveryResponse:
        """Enforces delivery state machine and validates GPS proximity."""
        delivery = await self.get_delivery(delivery_id)
        driver_prof = await self.driver_service.get_driver_profile(driver_user_id)

        # Enforce that only the assigned driver can invoke execution transitions
        if delivery.driver_id != driver_prof.id:
            raise ForbiddenException("You are not the assigned driver for this delivery.")

        # State transition validation (Section 13)
        allowed_next = self.VALID_TRANSITIONS.get(delivery.status.value, [])
        if target_status.value not in allowed_next:
            raise ConflictException(
                f"Invalid transition from '{delivery.status.value}' to '{target_status.value}'.",
                error_code="INVALID_STATE_TRANSITION",
            )

        now_iso = datetime.now(timezone.utc).isoformat()
        fields_to_update: Dict[str, Any] = {"status": target_status.value}
        proximity_audit_data: Optional[Dict[str, Any]] = None

        # Fetch donation to get donor_id for notifications
        donation = await self.db.get_by_id("donations", delivery.donation_id, id_column="id")
        donor_user_id = donation.get("donor_id") if donation else None

        # Operational status actions:
        if target_status == DeliveryStatus.ARRIVING_PICKUP:
            # GPS proximity check on pickup
            if proximity and proximity.latitude is not None and proximity.longitude is not None and delivery.stops:
                pickup_loc = await self.db.get_by_id("locations", delivery.stops[0].location_id, id_column="id")
                if pickup_loc:
                    dist = self.routing.calculate_distance(
                        proximity.latitude, proximity.longitude,
                        float(pickup_loc["latitude"]), float(pickup_loc["longitude"])
                    )
                    proximity_audit_data = {
                        "latitude": proximity.latitude,
                        "longitude": proximity.longitude,
                        "distance_to_target_km": round(dist, 3),
                        "timestamp": now_iso,
                    }
                    if dist > self.PICKUP_PROXIMITY_RADIUS_KM:
                        raise ConflictException(
                            f"Driver is outside the pickup proximity threshold of {int(self.PICKUP_PROXIMITY_RADIUS_KM * 1000)}m (current distance: {int(dist * 1000)}m).",
                            error_code="PROXIMITY_CHECK_FAILED",
                        )

            # Update pickup stop to ARRIVED
            if delivery.stops:
                await self.db.update_by_id(
                    "delivery_stops",
                    delivery.stops[0].id,
                    {"status": DeliveryStopStatus.ARRIVED.value, "arrived_at": now_iso},
                )
            if donor_user_id:
                await self.notification.notify_event(
                    user_id=donor_user_id,
                    event_type="DELIVERY_STATUS",
                    title="Driver Arriving at Pickup",
                    message="The delivery partner is arriving at your pickup location.",
                    data={"delivery_id": delivery_id, "event_key": "ARRIVING_PICKUP"},
                )

        elif target_status == DeliveryStatus.PICKED_UP:
            fields_to_update["picked_up_at"] = now_iso
            # Mark pickup stop as COMPLETED
            if delivery.stops:
                await self.db.update_by_id(
                    "delivery_stops",
                    delivery.stops[0].id,
                    {"status": DeliveryStopStatus.COMPLETED.value, "completed_at": now_iso},
                )
            if donor_user_id:
                await self.notification.notify_event(
                    user_id=donor_user_id,
                    event_type="DELIVERY_STATUS",
                    title="Food Picked Up",
                    message="Food has been verified and picked up by the delivery partner.",
                    data={"delivery_id": delivery_id, "event_key": "PICKED_UP"},
                )

        elif target_status == DeliveryStatus.IN_TRANSIT:
            for s in delivery.stops:
                if s.receiver_id:
                    receiver_prof = await self.db.get_by_id("receiver_profiles", s.receiver_id, id_column="id")
                    if receiver_prof:
                        await self.notification.notify_event(
                            user_id=receiver_prof["user_id"],
                            event_type="DELIVERY_STATUS",
                            title="Food Rescue On The Way",
                            message="Food rescue is in transit to your distribution center.",
                            data={"delivery_id": delivery_id, "event_key": "IN_TRANSIT"},
                        )

        elif target_status == DeliveryStatus.AT_STOP:
            # Find the active delivery stop (specified by stop_id or first non-completed delivery stop)
            target_stop = None
            if stop_id:
                target_stop = next((s for s in delivery.stops if s.id == stop_id), None)
            if not target_stop:
                target_stop = next((s for s in delivery.stops if s.stop_type == DeliveryStopType.DELIVERY and s.status != DeliveryStopStatus.COMPLETED), None)

            if target_stop and proximity and proximity.latitude is not None and proximity.longitude is not None:
                stop_loc = await self.db.get_by_id("locations", target_stop.location_id, id_column="id")
                if stop_loc:
                    dist = self.routing.calculate_distance(
                        proximity.latitude, proximity.longitude,
                        float(stop_loc["latitude"]), float(stop_loc["longitude"])
                    )
                    proximity_audit_data = {
                        "latitude": proximity.latitude,
                        "longitude": proximity.longitude,
                        "distance_to_target_km": round(dist, 3),
                        "timestamp": now_iso,
                    }
                    if dist > self.STOP_PROXIMITY_RADIUS_KM:
                        raise ConflictException(
                            f"Driver is outside the delivery stop proximity threshold of {int(self.STOP_PROXIMITY_RADIUS_KM * 1000)}m (current distance: {int(dist * 1000)}m).",
                            error_code="PROXIMITY_CHECK_FAILED",
                        )

            if target_stop:
                await self.db.update_by_id(
                    "delivery_stops",
                    target_stop.id,
                    {"status": DeliveryStopStatus.ARRIVED.value, "arrived_at": now_iso},
                )
                if target_stop.receiver_id:
                    receiver_prof = await self.db.get_by_id("receiver_profiles", target_stop.receiver_id, id_column="id")
                    if receiver_prof:
                        await self.notification.notify_event(
                            user_id=receiver_prof["user_id"],
                            event_type="DELIVERY_STATUS",
                            title="Driver Arrived",
                            message="Delivery partner has arrived at your distribution center.",
                            data={"delivery_id": delivery_id, "event_key": f"ARRIVED_{target_stop.id}"},
                        )

        elif target_status == DeliveryStatus.DELIVERED:
            fields_to_update["completed_at"] = now_iso
            # Free driver back to AVAILABLE
            await self.db.update_by_id(
                "driver_profiles",
                driver_prof.id,
                {"availability_status": DriverAvailabilityStatus.AVAILABLE.value},
            )
            # Mark all delivery stops as COMPLETED
            for s in delivery.stops:
                if s.stop_type == DeliveryStopType.DELIVERY:
                    await self.db.update_by_id(
                        "delivery_stops",
                        s.id,
                        {"status": DeliveryStopStatus.COMPLETED.value, "completed_at": now_iso},
                    )
            if donor_user_id:
                await self.notification.notify_event(
                    user_id=donor_user_id,
                    event_type="DELIVERY_STATUS",
                    title="Food Rescue Completed",
                    message="Your surplus food donation has been successfully delivered!",
                    data={"delivery_id": delivery_id, "event_key": "DELIVERED"},
                )

        updated = await self.db.update_by_id("deliveries", delivery_id, fields_to_update)
        audit_new_vals = {"status": target_status.value}
        if proximity_audit_data:
            audit_new_vals["proximity"] = proximity_audit_data

        await self.audit.log_event(
            action="DELIVERY_STATUS_CHANGED",
            entity_type="deliveries",
            entity_id=delivery_id,
            user_id=driver_user_id,
            old_values={"status": delivery.status.value},
            new_values=audit_new_vals,
        )
        return await self.get_delivery(delivery_id)

    async def get_driver_deliveries(self, driver_user_id: str) -> List[DeliveryResponse]:
        """Lists deliveries assigned to this driver."""
        driver_prof = await self.driver_service.get_driver_profile(driver_user_id)
        records = await self.db.query("deliveries", params={"driver_id": f"eq.{driver_prof.id}"})
        return [await self.get_delivery(d["id"]) for d in records]
