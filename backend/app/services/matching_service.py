"""Deterministic Food Rescue Matching Engine."""

from datetime import datetime, timedelta, timezone
import logging
from typing import Any, Dict, List, Optional, Tuple
import uuid
from app.db.supabase import SupabaseClient
from app.schemas.match import MatchResponse, MatchStatus, PriorityLabel
from app.schemas.need import DietType, NeedStatus
from app.services.audit_service import AuditService
from app.services.notification_service import NotificationService
from app.services.routing_provider import RoutingProvider, get_routing_provider
from app.utils.exceptions import ForbiddenException, NotFoundException, ValidationException

logger = logging.getLogger("annasetu.services.matching")


class MatchingService:
    """Core deterministic matching and rescue priority engine.

    Strictly deterministic - does NOT use AI for operational eligibility or scoring.
    """

    # Configurable weights (Section 7)
    WEIGHT_EXPIRY = 0.30
    WEIGHT_ETA = 0.25
    WEIGHT_DISTANCE = 0.20
    WEIGHT_FULFILLMENT = 0.15
    WEIGHT_ROUTE = 0.10

    def __init__(
        self,
        db: SupabaseClient,
        routing: Optional[RoutingProvider] = None,
    ):
        self.db = db
        self.routing = routing or get_routing_provider()
        self.notification = NotificationService(db)
        self.audit = AuditService(db)

    @staticmethod
    def _is_diet_compatible(donation_diet: str, need_diet: str) -> bool:
        """Determines if food donation diet type satisfies receiver need diet requirement."""
        d_diet = donation_diet.upper()
        n_diet = need_diet.upper()

        if n_diet == "MIXED":
            return True
        if n_diet == "VEGETARIAN":
            return d_diet == "VEGETARIAN"
        if n_diet == "NON_VEGETARIAN":
            return d_diet == "NON_VEGETARIAN"
        return False

    @staticmethod
    def _parse_iso(timestamp_str: str) -> datetime:
        clean_str = timestamp_str.replace("Z", "+00:00")
        dt = datetime.fromisoformat(clean_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt

    def calculate_priority_score(
        self,
        distance_km: float,
        travel_minutes: int,
        expiry_buffer_minutes: int,
        fulfillable_kg: float,
        required_kg: float,
        capacity_kg: float,
        route_feasible: bool,
    ) -> Tuple[float, Dict[str, Any], str, PriorityLabel]:
        """Calculates deterministic rescue priority score [0, 100] and structured breakdown."""
        # 1. Expiry urgency score (shorter buffer = higher urgency)
        if expiry_buffer_minutes <= 0:
            expiry_score = 0.0
        else:
            # 12 hours (720 mins) maximum baseline
            expiry_score = max(0.0, min(100.0, 100.0 - (expiry_buffer_minutes / 720.0) * 80.0))

        # 2. ETA efficiency score
        eta_score = max(0.0, min(100.0, 100.0 - (travel_minutes / 60.0) * 100.0))

        # 3. Distance efficiency score (25km baseline)
        distance_score = max(0.0, min(100.0, 100.0 - (distance_km / 25.0) * 100.0))

        # 4. Need fulfillment potential
        fulfillment_pct = (fulfillable_kg / required_kg) * 100.0 if required_kg > 0 else 0.0
        fulfillment_score = max(0.0, min(100.0, fulfillment_pct))

        # 5. Route feasibility score
        route_score = 100.0 if route_feasible else 0.0

        raw_priority = (
            expiry_score * self.WEIGHT_EXPIRY
            + eta_score * self.WEIGHT_ETA
            + distance_score * self.WEIGHT_DISTANCE
            + fulfillment_score * self.WEIGHT_FULFILLMENT
            + route_score * self.WEIGHT_ROUTE
        )
        priority_score = round(max(0.0, min(100.0, raw_priority)), 1)

        # Operational labels from fixed thresholds (Section 10)
        if priority_score >= 75.0:
            priority_label = PriorityLabel.HIGH
            label_text = "High"
        elif priority_score >= 50.0:
            priority_label = PriorityLabel.MEDIUM
            label_text = "Medium"
        else:
            priority_label = PriorityLabel.LOW
            label_text = "Low"

        # Structured breakdown (Section 8)
        breakdown = {
            "distance_km": distance_km,
            "estimated_travel_minutes": travel_minutes,
            "expiry_buffer_minutes": expiry_buffer_minutes,
            "fulfillment_percent": round(fulfillment_pct, 1),
            "capacity_available_kg": capacity_kg,
            "route_feasible": route_feasible,
            "expiry_score": round(expiry_score, 1),
            "eta_score": round(eta_score, 1),
            "distance_score": round(distance_score, 1),
            "fulfillment_score": round(fulfillment_score, 1),
            "route_score": round(route_score, 1),
            "priority_score": priority_score,
        }

        # Deterministic human-readable explanation
        hours = expiry_buffer_minutes // 60
        mins = expiry_buffer_minutes % 60
        time_desc = f"{hours}h {mins}m" if hours > 0 else f"{mins}m"
        explanation = (
            f"{label_text} rescue priority: donation expires in {time_desc}, "
            f"receiver is {distance_km} km away (ETA {travel_minutes} mins), "
            f"and can fulfill {fulfillment_pct:.0f}% of the required food need."
        )

        return priority_score, breakdown, explanation, priority_label

    async def generate_matches_for_donation(
        self,
        donation_id: str,
        donor_id: Optional[str] = None,
    ) -> List[MatchResponse]:
        """Discovers eligible needs and generates deterministic matches for a donation."""
        donation = await self.db.get_by_id("donations", donation_id, id_column="id")
        if not donation:
            raise NotFoundException("Donation not found.", error_code="DONATION_NOT_FOUND")

        if donor_id and donation.get("donor_id") != donor_id:
            raise ForbiddenException("Access forbidden. You do not own this donation.", error_code="DONATION_FORBIDDEN")

        # Hard Eligibility 1: Donation is POSTED or active
        if donation.get("status") not in ("POSTED", "MATCHING", "MATCHED", "ALLOCATED"):
            raise ValidationException(
                f"Donation is in '{donation.get('status')}' status and cannot be matched.",
                error_code="DONATION_NOT_MATCHABLE",
            )

        remaining_donation_kg = float(donation.get("remaining_quantity_kg", 0.0))
        if remaining_donation_kg <= 0:
            return []

        # Get donation pickup location
        pickup_loc_id = donation.get("pickup_location_id")
        pickup_loc = await self.db.get_by_id("locations", pickup_loc_id, id_column="id")
        if not pickup_loc:
            raise ValidationException("Pickup location missing coordinates or record.", error_code="PICKUP_LOCATION_MISSING")

        p_lat = float(pickup_loc.get("latitude", 28.6139))
        p_lon = float(pickup_loc.get("longitude", 77.2090))

        # Query all active or partially fulfilled needs
        active_needs = await self.db.query("ngo_needs", params={"status": "in.(ACTIVE,PARTIALLY_FULFILLED)"})

        matched_results: List[Dict[str, Any]] = []
        now = datetime.now(timezone.utc)
        rescue_deadline = self._parse_iso(donation["rescue_deadline"])

        # Hard Eligibility 7: Available before rescue deadline
        avail_from = self._parse_iso(donation["available_from"])
        if avail_from >= rescue_deadline or rescue_deadline <= now:
            return []

        for need in active_needs:
            # Hard Eligibility 5: Need has remaining quantity
            rem_need_kg = float(need.get("remaining_quantity_kg", 0.0))
            if rem_need_kg <= 0:
                continue

            # Hard Eligibility 11: Minimum allocatable quantity
            min_need_kg = float(need.get("minimum_quantity_kg", 1.0))
            if remaining_donation_kg < min_need_kg:
                continue

            # Hard Eligibility 3: Diet compatibility
            if not self._is_diet_compatible(donation.get("diet_type", ""), need.get("diet_type", "")):
                continue

            # Hard Eligibility 4: Food category compatibility
            if donation.get("food_category_id") != need.get("food_category_id"):
                continue

            # Hard Eligibility 6: Receiving capacity
            rec_capacity_kg = float(need.get("receiving_capacity_kg", 0.0))
            if rec_capacity_kg < min_need_kg:
                continue

            # Hard Eligibility 10: Receiving location
            need_loc = await self.db.get_by_id("locations", need["location_id"], id_column="id")
            if not need_loc:
                continue

            n_lat = float(need_loc.get("latitude", 28.6139))
            n_lon = float(need_loc.get("longitude", 77.2090))

            # Routing calculations
            dist_km = self.routing.calculate_distance(p_lat, p_lon, n_lat, n_lon)
            route_feasible = self.routing.check_route_feasibility(dist_km)
            travel_mins = self.routing.estimate_travel_time(dist_km)

            estimated_arrival = max(now, avail_from) + timedelta(minutes=travel_mins)
            required_by = self._parse_iso(need["required_by"])

            # Hard Eligibility 9: Arrival must occur before deadline and required_by
            if estimated_arrival >= rescue_deadline:
                continue
            if estimated_arrival >= required_by:
                continue

            expiry_buffer_mins = int((rescue_deadline - estimated_arrival).total_seconds() / 60)
            if expiry_buffer_mins <= 0:
                continue

            # Fulfillable quantity is the bottleneck across available surplus, need remaining, and physical capacity
            fulfillable_kg = min(remaining_donation_kg, rem_need_kg, rec_capacity_kg)
            if fulfillable_kg < min_need_kg:
                continue

            priority_score, breakdown, explanation, priority_label = self.calculate_priority_score(
                distance_km=dist_km,
                travel_minutes=travel_mins,
                expiry_buffer_minutes=expiry_buffer_mins,
                fulfillable_kg=fulfillable_kg,
                required_kg=float(need["required_quantity_kg"]),
                capacity_kg=rec_capacity_kg,
                route_feasible=route_feasible,
            )

            # Check if match already exists for (donation_id, need_id) to avoid duplicates
            existing_matches = await self.db.query(
                "matches",
                params={"donation_id": f"eq.{donation_id}", "need_id": f"eq.{need['id']}"},
            )

            match_payload = {
                "donation_id": donation_id,
                "need_id": need["id"],
                "distance_km": dist_km,
                "estimated_travel_minutes": travel_mins,
                "estimated_arrival_at": estimated_arrival.isoformat(),
                "expiry_buffer_minutes": expiry_buffer_mins,
                "fulfillable_quantity_kg": fulfillable_kg,
                "fulfillment_percent": breakdown["fulfillment_percent"],
                "distance_score": breakdown["distance_score"],
                "eta_score": breakdown["eta_score"],
                "expiry_score": breakdown["expiry_score"],
                "quantity_score": breakdown["fulfillment_score"],
                "capacity_score": 100.0,
                "route_score": breakdown["route_score"],
                "priority_score": priority_score,
                "priority_breakdown": breakdown,
                "status": MatchStatus.PROPOSED.value,
            }

            if existing_matches:
                match_id = existing_matches[0]["id"]
                persisted = await self.db.update_by_id("matches", match_id, match_payload, id_column="id")
            else:
                match_id = str(uuid.uuid4())
                match_payload["id"] = match_id
                persisted = await self.db.insert("matches", match_payload)

            persisted["explanation"] = explanation
            persisted["priority_label"] = priority_label.value
            matched_results.append(persisted)

            # Notify receiver if HIGH/MEDIUM priority
            await self.notification.notify_receiver_match(
                receiver_user_id=need["receiver_id"],
                match_id=match_id,
                donation_id=donation_id,
                fulfillable_quantity_kg=fulfillable_kg,
                diet_type=donation.get("diet_type", ""),
                priority_label=priority_label.value,
            )

        # Update donation status to MATCHED if matches found and currently POSTED
        if matched_results and donation.get("status") == "POSTED":
            await self.db.update_by_id("donations", donation_id, {"status": "MATCHED"}, id_column="id")

        await self.audit.log_event(
            "MATCHES_GENERATED",
            "donations",
            donation_id,
            user_id=donor_id,
            new_values={"matches_count": len(matched_results)},
        )

        # Sort matches (Section 10):
        # 1. priority_score DESC
        # 2. expiry_score DESC
        # 3. estimated_arrival_at ASC
        # 4. distance_km ASC
        matched_results.sort(
            key=lambda m: (
                -float(m.get("priority_score", 0)),
                -float(m.get("expiry_score", 0)),
                m.get("estimated_arrival_at", ""),
                float(m.get("distance_km", 0)),
            )
        )

        return [MatchResponse(**m) for m in matched_results]

    async def get_matches_for_donation(
        self,
        donation_id: str,
        donor_id: Optional[str] = None,
    ) -> List[MatchResponse]:
        """Fetch existing matches for a donation."""
        donation = await self.db.get_by_id("donations", donation_id, id_column="id")
        if not donation:
            raise NotFoundException("Donation not found.", error_code="DONATION_NOT_FOUND")

        if donor_id and donation.get("donor_id") != donor_id:
            raise ForbiddenException("Access forbidden. You do not own this donation.", error_code="DONATION_FORBIDDEN")

        records = await self.db.query(
            "matches",
            params={"donation_id": f"eq.{donation_id}"},
            order="priority_score.desc",
        )

        results = []
        for r in records:
            score = float(r.get("priority_score", 0.0))
            label = PriorityLabel.HIGH if score >= 75 else (PriorityLabel.MEDIUM if score >= 50 else PriorityLabel.LOW)
            r["priority_label"] = label.value
            r["explanation"] = (
                f"{label.value.capitalize()} rescue priority: {r.get('fulfillable_quantity_kg', 0):.1f} kg fulfillable, "
                f"{r.get('distance_km', 0):.1f} km away (ETA {r.get('estimated_travel_minutes', 0)} mins)."
            )
            results.append(MatchResponse(**r))
        return results

    async def get_matches_for_need(
        self,
        need_id: str,
        receiver_id: Optional[str] = None,
    ) -> List[MatchResponse]:
        """Fetch existing matches for an NGO need."""
        need = await self.db.get_by_id("ngo_needs", need_id, id_column="id")
        if not need:
            raise NotFoundException("NGO Need not found.", error_code="NEED_NOT_FOUND")

        if receiver_id and need.get("receiver_id") != receiver_id:
            raise ForbiddenException("Access forbidden. You do not own this need.", error_code="NEED_FORBIDDEN")

        records = await self.db.query(
            "matches",
            params={"need_id": f"eq.{need_id}"},
            order="priority_score.desc",
        )

        results = []
        for r in records:
            score = float(r.get("priority_score", 0.0))
            label = PriorityLabel.HIGH if score >= 75 else (PriorityLabel.MEDIUM if score >= 50 else PriorityLabel.LOW)
            r["priority_label"] = label.value
            r["explanation"] = (
                f"{label.value.capitalize()} rescue opportunity: {r.get('fulfillable_quantity_kg', 0):.1f} kg surplus food "
                f"from nearby donor ({r.get('distance_km', 0):.1f} km)."
            )
            results.append(MatchResponse(**r))
        return results
