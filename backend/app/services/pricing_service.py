"""Delivery Pricing and Financial Breakdown Service."""

from decimal import Decimal, ROUND_HALF_UP
import logging
from typing import Any, Dict, Optional
from app.core.config import settings
from app.db.supabase import SupabaseClient
from app.schemas.pricing import DeliveryPricingResponse
from app.utils.exceptions import NotFoundException

logger = logging.getLogger("annasetu.services.pricing")

TWO_PLACES = Decimal("0.01")


class PricingService:
    """Service for deterministic delivery pricing, platform fee, and driver payout calculation."""

    # Configurable platform fallback pricing constants
    DEFAULT_BASE_FARE = Decimal("50.00")
    DEFAULT_PER_KM_RATE = Decimal("12.00")
    DEFAULT_PER_MINUTE_RATE = Decimal("1.50")
    DEFAULT_STOP_FEE = Decimal("30.00")
    DEFAULT_PLATFORM_FEE_PERCENT = Decimal("12.00")  # Configurable 12% fee

    DEFAULT_PAYOUT_MULTIPLIER = Decimal("0.85")
    DEFAULT_MINIMUM_DRIVER_PAYOUT = Decimal("80.00")

    def __init__(self, db: SupabaseClient):
        self.db = db

    @staticmethod
    def _quantize(val: Decimal) -> Decimal:
        return val.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)

    async def get_active_pricing_rule(self) -> Dict[str, Decimal]:
        """Loads active pricing rule from database, falling back to platform defaults."""
        rules = await self.db.query("pricing_rules", params={"is_active": "eq.true"})
        if rules:
            r = rules[0]
            return {
                "base_fare": Decimal(str(r.get("base_fare", self.DEFAULT_BASE_FARE))),
                "per_km_rate": Decimal(str(r.get("per_km_rate", self.DEFAULT_PER_KM_RATE))),
                "per_minute_rate": Decimal(str(r.get("per_minute_rate", self.DEFAULT_PER_MINUTE_RATE))),
                "stop_fee": Decimal(str(r.get("stop_fee", self.DEFAULT_STOP_FEE))),
                "platform_fee_percent": Decimal(str(r.get("platform_fee_percent", self.DEFAULT_PLATFORM_FEE_PERCENT))),
            }
        return {
            "base_fare": self.DEFAULT_BASE_FARE,
            "per_km_rate": self.DEFAULT_PER_KM_RATE,
            "per_minute_rate": self.DEFAULT_PER_MINUTE_RATE,
            "stop_fee": self.DEFAULT_STOP_FEE,
            "platform_fee_percent": self.DEFAULT_PLATFORM_FEE_PERCENT,
        }

    async def get_vehicle_pricing(self, vehicle_type: str) -> Dict[str, Decimal]:
        """Loads vehicle pricing multipliers from database."""
        v_prices = await self.db.query(
            "vehicle_pricing",
            params={"vehicle_type": f"eq.{vehicle_type.lower()}", "is_active": "eq.true"},
        )
        if v_prices:
            vp = v_prices[0]
            return {
                "payout_multiplier": Decimal(str(vp.get("payout_multiplier", self.DEFAULT_PAYOUT_MULTIPLIER))),
                "minimum_driver_payout": Decimal(str(vp.get("minimum_driver_payout", self.DEFAULT_MINIMUM_DRIVER_PAYOUT))),
            }
        return {
            "payout_multiplier": self.DEFAULT_PAYOUT_MULTIPLIER,
            "minimum_driver_payout": self.DEFAULT_MINIMUM_DRIVER_PAYOUT,
        }

    async def calculate_delivery_pricing(
        self,
        delivery_id: str,
        snapshot: bool = True,
    ) -> DeliveryPricingResponse:
        """Calculates exact pricing breakdown for a delivery using Decimal arithmetic."""
        delivery = await self.db.get_by_id("deliveries", delivery_id, id_column="id")
        if not delivery:
            raise NotFoundException("Delivery not found.", error_code="DELIVERY_NOT_FOUND")

        # Count delivery stops (stop_type == DELIVERY)
        stops = await self.db.query("delivery_stops", params={"delivery_id": f"eq.{delivery_id}"})
        delivery_stops_count = sum(1 for s in stops if s.get("stop_type") == "DELIVERY")
        if delivery_stops_count == 0:
            delivery_stops_count = 1

        dist_km = Decimal(str(delivery.get("total_distance_km") or 10.0))
        dur_mins = Decimal(str(delivery.get("estimated_duration_minutes") or 30))
        v_type = str(delivery.get("vehicle_type") or "auto").lower()

        rule = await self.get_active_pricing_rule()
        veh_rule = await self.get_vehicle_pricing(v_type)

        # Monetary component calculations
        base_fare = self._quantize(rule["base_fare"])
        distance_charge = self._quantize(dist_km * rule["per_km_rate"])
        time_charge = self._quantize(dur_mins * rule["per_minute_rate"])
        stop_fees = self._quantize(Decimal(str(delivery_stops_count)) * rule["stop_fee"])

        # Delivery Charge = Base + Distance + Time + Stop Fees
        delivery_charge = self._quantize(base_fare + distance_charge + time_charge + stop_fees)

        # Platform Fee = Delivery Charge * Platform Fee Percent / 100
        platform_fee_percent = rule["platform_fee_percent"]
        platform_fee = self._quantize(delivery_charge * (platform_fee_percent / Decimal("100.00")))

        # NGO Total = Delivery Charge + Platform Fee
        ngo_total = self._quantize(delivery_charge + platform_fee)

        # Driver Payout = max(minimum_driver_payout, delivery_charge * payout_multiplier)
        raw_driver_payout = self._quantize(delivery_charge * veh_rule["payout_multiplier"])
        driver_payout = max(self._quantize(veh_rule["minimum_driver_payout"]), raw_driver_payout)

        # Snapshot calculated pricing to delivery record so historical commitments are preserved
        if snapshot:
            await self.db.update_by_id(
                "deliveries",
                delivery_id,
                {
                    "delivery_charge": float(delivery_charge),
                    "platform_fee": float(platform_fee),
                    "driver_payout": float(driver_payout),
                    "ngo_total": float(ngo_total),
                },
            )

        return DeliveryPricingResponse(
            delivery_id=delivery_id,
            base_fare=base_fare,
            distance_km=float(dist_km),
            distance_charge=distance_charge,
            duration_minutes=int(dur_mins),
            time_charge=time_charge,
            stop_count=delivery_stops_count,
            stop_fees=stop_fees,
            delivery_charge=delivery_charge,
            platform_fee_percent=platform_fee_percent,
            platform_fee=platform_fee,
            ngo_total=ngo_total,
            driver_payout=driver_payout,
            currency="INR",
        )
