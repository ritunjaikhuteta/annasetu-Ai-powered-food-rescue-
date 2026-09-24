"""Multi-Stop Route Evaluation Service."""

from datetime import datetime, timedelta, timezone
import itertools
import logging
from typing import Any, Dict, List, Optional, Tuple
from app.services.routing_provider import RoutingProvider, get_routing_provider
from app.utils.exceptions import ConflictException

logger = logging.getLogger("annasetu.services.routing")


class RoutingService:
    """Service evaluating multi-stop logistics routes deterministically."""

    def __init__(self, routing: Optional[RoutingProvider] = None):
        self.routing = routing or get_routing_provider()

    @staticmethod
    def _parse_iso(timestamp_str: str) -> datetime:
        clean = timestamp_str.replace("Z", "+00:00")
        dt = datetime.fromisoformat(clean)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt

    def evaluate_multistop_route(
        self,
        pickup_lat: float,
        pickup_lon: float,
        stops_info: List[Dict[str, Any]],
        start_time: datetime,
        rescue_deadline: datetime,
        service_time_mins: int = 10,
    ) -> Dict[str, Any]:
        """Evaluates permutations for up to 3 delivery stops and chooses the optimal feasible sequence.

        Args:
            pickup_lat: Donor latitude
            pickup_lon: Donor longitude
            stops_info: List of receiver stop dicts (lat, lon, required_by, etc.)
            start_time: Estimated route start time
            rescue_deadline: Donation rescue deadline
            service_time_mins: Handling time per delivery stop (default 10 mins)

        Returns:
            Dict containing:
                - total_distance_km
                - estimated_duration_minutes
                - ordered_stops
        Raises:
            ConflictException if no sequence can meet the deadlines.
        """
        if not stops_info:
            return {
                "total_distance_km": 0.0,
                "estimated_duration_minutes": 0,
                "ordered_stops": [],
            }

        if len(stops_info) > 3:
            raise ConflictException("A single rescue delivery supports a maximum of 3 NGO stops.")

        best_route: Optional[Dict[str, Any]] = None
        best_duration = float("inf")

        # Evaluate all permutations (3! = 6 maximum)
        for perm in itertools.permutations(stops_info):
            current_time = start_time
            curr_lat, curr_lon = pickup_lat, pickup_lon
            perm_distance = 0.0
            ordered_stops = []
            is_feasible = True

            for seq_idx, stop in enumerate(perm, start=2):
                s_lat = float(stop["latitude"])
                s_lon = float(stop["longitude"])
                leg_dist = self.routing.calculate_distance(curr_lat, curr_lon, s_lat, s_lon)
                travel_mins = self.routing.estimate_travel_time(leg_dist)

                arrival_time = current_time + timedelta(minutes=travel_mins)
                req_by = self._parse_iso(stop["required_by"])

                # Hard feasibility checks:
                # 1. Arrival must be before donation rescue deadline
                # 2. Arrival must be before receiver required_by
                if arrival_time > rescue_deadline or arrival_time > req_by:
                    is_feasible = False
                    break

                ordered_stops.append({
                    "sequence_number": seq_idx,
                    "stop_type": "DELIVERY",
                    "location_id": stop["location_id"],
                    "receiver_id": stop.get("receiver_id"),
                    "allocation_id": stop.get("allocation_id"),
                    "quantity_kg": stop.get("quantity_kg", 0.0),
                    "distance_from_prev_km": leg_dist,
                    "estimated_arrival": arrival_time.isoformat(),
                    "status": "PENDING",
                })

                perm_distance += leg_dist
                # Progress time with handling buffer
                current_time = arrival_time + timedelta(minutes=service_time_mins)
                curr_lat, curr_lon = s_lat, s_lon

            if is_feasible:
                total_duration = int((current_time - start_time).total_seconds() / 60)
                if total_duration < best_duration:
                    best_duration = total_duration
                    best_route = {
                        "total_distance_km": round(perm_distance, 2),
                        "estimated_duration_minutes": total_duration,
                        "ordered_stops": ordered_stops,
                    }

        if not best_route:
            raise ConflictException(
                message="No feasible route can reach all selected receivers before the rescue deadline.",
                error_code="NO_FEASIBLE_ROUTE",
            )

        return best_route
