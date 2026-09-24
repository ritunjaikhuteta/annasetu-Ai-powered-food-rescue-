"""Driver (Delivery Partner) Domain Service."""

from datetime import datetime, timedelta, timezone
import logging
from typing import Any, Dict, List, Optional
import uuid
from app.db.supabase import SupabaseClient
from app.schemas.common import VerificationStatus
from app.schemas.driver import (
    DriverAvailabilityStatus,
    DriverLocationResponse,
    DriverLocationUpdate,
    DriverProfileResponse,
    DriverProfileUpdate,
    EligibleDriverResponse,
)
from app.services.routing_provider import RoutingProvider, get_routing_provider
from app.utils.exceptions import ForbiddenException, NotFoundException, ValidationException

logger = logging.getLogger("annasetu.services.driver")


class DriverService:
    """Service managing delivery partner profiles, telemetry, and discovery."""

    # Configurable platform vehicle catalog capacities (platform/demo values, not legal limits)
    DEFAULT_VEHICLE_CAPACITIES: Dict[str, float] = {
        "motorcycle": 15.0,
        "scooter": 15.0,
        "auto": 75.0,
        "car": 150.0,
        "van": 500.0,
        "pickup": 500.0,
        "small-truck": 1500.0,
        "truck": 5000.0,
    }

    def __init__(
        self,
        db: SupabaseClient,
        routing: Optional[RoutingProvider] = None,
    ):
        self.db = db
        self.routing = routing or get_routing_provider()

    async def get_driver_profile(self, user_id: str) -> DriverProfileResponse:
        record = await self.db.get_by_id("driver_profiles", user_id, id_column="user_id")
        if not record:
            raise NotFoundException("Driver profile record not found.", error_code="DRIVER_PROFILE_NOT_FOUND")

        raw_status = (record.get("verification_status") or "PENDING").upper()
        try:
            status = VerificationStatus(raw_status)
        except ValueError:
            status = VerificationStatus.PENDING

        raw_avail = (record.get("availability_status") or "AVAILABLE").upper()
        try:
            avail = DriverAvailabilityStatus(raw_avail)
        except ValueError:
            avail = DriverAvailabilityStatus.AVAILABLE

        return DriverProfileResponse(
            id=record["id"],
            user_id=record["user_id"],
            driving_license_number=record.get("driving_license_number"),
            vehicle_type=record.get("vehicle_type"),
            vehicle_number=record.get("vehicle_number"),
            vehicle_capacity_kg=record.get("vehicle_capacity_kg"),
            has_refrigeration=record.get("has_refrigeration", False),
            is_online=record.get("is_online", False),
            availability_status=avail,
            current_latitude=record.get("current_latitude"),
            current_longitude=record.get("current_longitude"),
            verification_status=status,
            created_at=str(record.get("created_at")) if record.get("created_at") else None,
            updated_at=str(record.get("updated_at")) if record.get("updated_at") else None,
        )

    async def update_driver_profile(self, user_id: str, payload: DriverProfileUpdate) -> DriverProfileResponse:
        fields_to_update: Dict[str, Any] = {}
        if payload.vehicle_type is not None:
            fields_to_update["vehicle_type"] = payload.vehicle_type.strip()
            # If vehicle_capacity_kg not specified, populate default from catalog
            if payload.vehicle_capacity_kg is None:
                fields_to_update["vehicle_capacity_kg"] = self.DEFAULT_VEHICLE_CAPACITIES.get(
                    payload.vehicle_type.lower(), 50.0
                )
        if payload.vehicle_number is not None:
            fields_to_update["vehicle_number"] = payload.vehicle_number.strip()
        if payload.vehicle_capacity_kg is not None:
            fields_to_update["vehicle_capacity_kg"] = payload.vehicle_capacity_kg
        if payload.has_refrigeration is not None:
            fields_to_update["has_refrigeration"] = payload.has_refrigeration
        if payload.is_online is not None:
            fields_to_update["is_online"] = payload.is_online
        if payload.availability_status is not None:
            fields_to_update["availability_status"] = payload.availability_status.value
        if payload.current_latitude is not None:
            fields_to_update["current_latitude"] = payload.current_latitude
        if payload.current_longitude is not None:
            fields_to_update["current_longitude"] = payload.current_longitude

        if not fields_to_update:
            return await self.get_driver_profile(user_id)

        await self.db.update_by_id("driver_profiles", user_id, fields_to_update, id_column="user_id")
        return await self.get_driver_profile(user_id)

    async def record_location(self, driver_user_id: str, payload: DriverLocationUpdate) -> DriverLocationResponse:
        """Records driver GPS telemetry into driver_locations and updates active profile coordinates."""
        driver_profile = await self.get_driver_profile(driver_user_id)

        now_str = datetime.now(timezone.utc).isoformat()
        loc_id = str(uuid.uuid4())
        location_record = {
            "id": loc_id,
            "driver_id": driver_profile.id,
            "latitude": payload.latitude,
            "longitude": payload.longitude,
            "accuracy_meters": payload.accuracy_meters,
            "recorded_at": now_str,
        }

        created = await self.db.insert("driver_locations", location_record)

        # Update latest coordinates on profile
        await self.db.update_by_id(
            "driver_profiles",
            driver_profile.id,
            {
                "current_latitude": payload.latitude,
                "current_longitude": payload.longitude,
            },
            id_column="id",
        )

        return DriverLocationResponse(
            id=created["id"],
            driver_id=created["driver_id"],
            latitude=created["latitude"],
            longitude=created["longitude"],
            accuracy_meters=created.get("accuracy_meters"),
            recorded_at=created.get("recorded_at", now_str),
        )

    async def find_eligible_drivers(
        self,
        delivery_quantity_kg: float,
        pickup_lat: float,
        pickup_lon: float,
        pickup_deadline: datetime,
        max_search_radius_km: float = 20.0,
    ) -> List[EligibleDriverResponse]:
        """Discovers and deterministically ranks eligible drivers.

        Hard eligibility criteria:
        1. Driver profile is VERIFIED
        2. availability_status = AVAILABLE
        3. Account is active (profiles.is_active = true)
        4. Valid vehicle type with capacity >= delivery_quantity_kg
        5. Known location within search radius
        6. Can reach pickup before deadline
        7. Not already assigned to another active delivery
        """
        all_drivers = await self.db.query(
            "driver_profiles",
            params={
                "verification_status": "eq.VERIFIED",
                "availability_status": "eq.AVAILABLE",
            },
        )

        active_deliveries = await self.db.query(
            "deliveries",
            params={"status": "in.(ACCEPTED,ARRIVING_PICKUP,PICKED_UP,IN_TRANSIT,AT_STOP)"},
        )
        busy_driver_ids = {d.get("driver_id") for d in active_deliveries if d.get("driver_id")}

        now = datetime.now(timezone.utc)
        eligible: List[EligibleDriverResponse] = []

        for d in all_drivers:
            driver_id = d["id"]
            user_id = d["user_id"]

            # Criteria 7: Not assigned to active delivery
            if driver_id in busy_driver_ids or user_id in busy_driver_ids:
                continue

            # Criteria 3: Profile is active
            user_profile = await self.db.get_by_id("profiles", user_id, id_column="id")
            if not user_profile or not user_profile.get("is_active", True):
                continue

            # Criteria 4: Vehicle capacity check
            v_type = (d.get("vehicle_type") or "auto").lower()
            v_capacity = float(
                d.get("vehicle_capacity_kg")
                or self.DEFAULT_VEHICLE_CAPACITIES.get(v_type, 50.0)
            )

            if v_capacity < delivery_quantity_kg:
                continue

            # Criteria 5: Location check
            d_lat = d.get("current_latitude")
            d_lon = d.get("current_longitude")
            if d_lat is None or d_lon is None:
                continue

            dist_km = self.routing.calculate_distance(float(d_lat), float(d_lon), pickup_lat, pickup_lon)
            if dist_km > max_search_radius_km:
                continue

            # Criteria 6: ETA feasibility before pickup deadline
            eta_mins = self.routing.estimate_travel_time(dist_km)
            estimated_arrival = now + timedelta(minutes=eta_mins)
            if estimated_arrival > pickup_deadline:
                continue

            eligible.append(
                EligibleDriverResponse(
                    id=driver_id,
                    driver_user_id=user_id,
                    name=user_profile.get("full_name") or "Verified Partner",
                    phone=user_profile.get("phone"),
                    vehicle_type=v_type,
                    vehicle_number=d.get("vehicle_number"),
                    vehicle_capacity_kg=v_capacity,
                    has_refrigeration=bool(d.get("has_refrigeration", False)),
                    distance_to_pickup_km=dist_km,
                    pickup_eta_minutes=eta_mins,
                    availability_status=DriverAvailabilityStatus.AVAILABLE,
                    verification_status=VerificationStatus.VERIFIED,
                )
            )

        # Deterministic Ranking:
        # 1. Pickup ETA ASC
        # 2. Distance to pickup ASC
        eligible.sort(key=lambda d: (d.pickup_eta_minutes, d.distance_to_pickup_km))
        return eligible
