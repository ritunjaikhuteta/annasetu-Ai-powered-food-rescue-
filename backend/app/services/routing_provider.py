"""Routing and Distance Provider Abstraction."""

from abc import ABC, abstractmethod
import math
from typing import Optional


class RoutingProvider(ABC):
    """Abstract base class for routing and travel time estimation."""

    @abstractmethod
    def calculate_distance(
        self,
        lat1: float,
        lon1: float,
        lat2: float,
        lon2: float,
    ) -> float:
        """Calculate distance in kilometers between two geographic coordinates."""
        pass

    @abstractmethod
    def estimate_travel_time(
        self,
        distance_km: float,
        speed_kmh: Optional[float] = None,
    ) -> int:
        """Estimate travel duration in minutes based on distance and route conditions."""
        pass

    @abstractmethod
    def check_route_feasibility(
        self,
        distance_km: float,
        max_feasible_km: float = 30.0,
    ) -> bool:
        """Check whether the route distance is within operational feasibility bounds."""
        pass


class HaversineRoutingProvider(RoutingProvider):
    """Deterministic routing provider using Haversine formula and urban speed profiles.

    Clearly labeled as estimated travel metrics for transparency.
    """

    DEFAULT_URBAN_SPEED_KMH = 25.0
    EARTH_RADIUS_KM = 6371.0

    def calculate_distance(
        self,
        lat1: float,
        lon1: float,
        lat2: float,
        lon2: float,
    ) -> float:
        """Calculate Haversine great-circle distance between two points."""
        d_lat = math.radians(lat2 - lat1)
        d_lon = math.radians(lon2 - lon1)
        a = (
            math.sin(d_lat / 2.0) ** 2
            + math.cos(math.radians(lat1))
            * math.cos(math.radians(lat2))
            * math.sin(d_lon / 2.0) ** 2
        )
        c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
        distance = self.EARTH_RADIUS_KM * c
        return round(distance, 2)

    def estimate_travel_time(
        self,
        distance_km: float,
        speed_kmh: Optional[float] = None,
    ) -> int:
        """Estimate urban travel time in minutes, adding a 5-minute buffer for pickup/handoff maneuvers."""
        effective_speed = speed_kmh or self.DEFAULT_URBAN_SPEED_KMH
        if effective_speed <= 0:
            effective_speed = self.DEFAULT_URBAN_SPEED_KMH

        # Travel time in hours converted to minutes + fixed 5 min base urban buffer
        travel_minutes = (distance_km / effective_speed) * 60.0
        total_estimated = int(math.ceil(travel_minutes + 5.0))
        return max(5, total_estimated)

    def check_route_feasibility(
        self,
        distance_km: float,
        max_feasible_km: float = 30.0,
    ) -> bool:
        """Determines if the distance is within the feasible food rescue delivery radius."""
        return distance_km <= max_feasible_km


# Default singleton instance
default_routing_provider = HaversineRoutingProvider()


def get_routing_provider() -> RoutingProvider:
    return default_routing_provider
