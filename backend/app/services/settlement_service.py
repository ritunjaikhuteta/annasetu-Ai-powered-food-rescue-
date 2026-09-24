"""Financial Settlement and Driver Payout Service."""

import asyncio
from collections import defaultdict
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
import logging
from typing import Any, Dict, Optional
import uuid
from app.db.supabase import SupabaseClient
from app.schemas.delivery import DeliveryStatus
from app.schemas.payment import PaymentRefundResponse
from app.schemas.wallet import TransactionStatus, TransactionType
from app.services.audit_service import AuditService
from app.services.notification_service import NotificationService
from app.services.pricing_service import PricingService
from app.services.wallet_service import WalletService
from app.utils.exceptions import ConflictException, NotFoundException, ValidationException

logger = logging.getLogger("annasetu.services.settlement")

TWO_PLACES = Decimal("0.01")
_settlement_locks: Dict[str, asyncio.Lock] = defaultdict(asyncio.Lock)


class SettlementService:
    """Service managing financial settlement, driver payouts, and administrative refunds."""

    def __init__(self, db: SupabaseClient):
        self.db = db
        self.pricing_service = PricingService(db)
        self.wallet_service = WalletService(db)
        self.audit = AuditService(db)
        self.notification = NotificationService(db)

    @staticmethod
    def _quantize(val: Decimal) -> Decimal:
        return val.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)

    async def settle_delivery(self, delivery_id: str) -> Dict[str, Any]:
        """Settles completed delivery: captures NGO payment, records platform fee, and credits driver payout."""
        delivery = await self.db.get_by_id("deliveries", delivery_id, id_column="id")
        if not delivery:
            raise NotFoundException("Delivery not found.", error_code="DELIVERY_NOT_FOUND")

        # 1. State machine check: must be DELIVERED
        if delivery.get("status") != DeliveryStatus.DELIVERED.value:
            raise ConflictException(
                f"Cannot settle incomplete delivery in status '{delivery.get('status')}'. Must be DELIVERED.",
                error_code="DELIVERY_NOT_DELIVERED",
            )

        # 2. Idempotency check: already settled
        if delivery.get("is_settled"):
            logger.info("Delivery %s is already settled (idempotent)", delivery_id)
            return {"delivery_id": delivery_id, "status": "ALREADY_SETTLED"}

        lock = _settlement_locks[delivery_id]
        async with lock:
            # Re-verify under lock
            deliv_current = await self.db.get_by_id("deliveries", delivery_id, id_column="id")
            if deliv_current.get("is_settled"):
                return {"delivery_id": delivery_id, "status": "ALREADY_SETTLED"}

            # Get pricing snapshot
            delivery_charge = self._quantize(Decimal(str(deliv_current.get("delivery_charge") or "100.00")))
            platform_fee = self._quantize(Decimal(str(deliv_current.get("platform_fee") or "12.00")))
            ngo_total = self._quantize(Decimal(str(deliv_current.get("ngo_total") or (delivery_charge + platform_fee))))
            driver_payout = self._quantize(Decimal(str(deliv_current.get("driver_payout") or "85.00")))

            now_iso = datetime.now(timezone.utc).isoformat()

            # 3. Capture NGO reservation if present
            reservations = await self.db.query(
                "wallet_reservations",
                params={"delivery_id": f"eq.{delivery_id}", "status": "eq.ACTIVE"},
            )

            if reservations:
                res_rec = reservations[0]
                ngo_wallet_id = res_rec["wallet_id"]
                ngo_wallet = await self.db.get_by_id("wallets", ngo_wallet_id, id_column="id")

                if ngo_wallet:
                    ngo_user_id = ngo_wallet["user_id"]
                    curr_bal = self._quantize(Decimal(str(ngo_wallet.get("balance", "0.00"))))
                    curr_res = self._quantize(Decimal(str(ngo_wallet.get("reserved_balance", "0.00"))))

                    new_bal = max(Decimal("0.00"), curr_bal - ngo_total)
                    new_res = max(Decimal("0.00"), curr_res - ngo_total)

                    # Update NGO wallet balance and release reservation hold
                    await self.db.update_by_id(
                        "wallets",
                        ngo_wallet_id,
                        {"balance": float(new_bal), "reserved_balance": float(new_res), "updated_at": now_iso},
                    )
                    await self.db.update_by_id(
                        "wallet_reservations",
                        res_rec["id"],
                        {"status": "CAPTURED", "updated_at": now_iso},
                    )

                    # Ledger entry: DELIVERY_CHARGE
                    await self.db.insert(
                        "transactions",
                        {
                            "id": str(uuid.uuid4()),
                            "wallet_id": ngo_wallet_id,
                            "user_id": ngo_user_id,
                            "type": TransactionType.DELIVERY_CHARGE.value,
                            "amount": float(delivery_charge),
                            "currency": "INR",
                            "status": TransactionStatus.COMPLETED.value,
                            "reference_id": delivery_id,
                            "reference_type": "delivery",
                            "description": f"Delivery charge for mission {delivery_id[:8]}",
                            "created_at": now_iso,
                        },
                    )

                    # Ledger entry: PLATFORM_FEE
                    await self.db.insert(
                        "transactions",
                        {
                            "id": str(uuid.uuid4()),
                            "wallet_id": ngo_wallet_id,
                            "user_id": ngo_user_id,
                            "type": TransactionType.PLATFORM_FEE.value,
                            "amount": float(platform_fee),
                            "currency": "INR",
                            "status": TransactionStatus.COMPLETED.value,
                            "reference_id": delivery_id,
                            "reference_type": "delivery",
                            "description": f"Platform fee (12%) for mission {delivery_id[:8]}",
                            "created_at": now_iso,
                        },
                    )

                    # Notify NGO
                    await self.notification.notify_event(
                        user_id=ngo_user_id,
                        event_type="DELIVERY_PAYMENT_CAPTURED",
                        title="Delivery Payment Processed",
                        message=f"₹{ngo_total} (Delivery: ₹{delivery_charge} + 12% Platform Fee: ₹{platform_fee}) captured for completed food rescue.",
                        data={"delivery_id": delivery_id, "amount": float(ngo_total)},
                    )

            # 4. Credit Driver Payout
            driver_id = deliv_current.get("driver_id")
            if driver_id:
                driver_prof = await self.db.get_by_id("driver_profiles", driver_id, id_column="id")
                if driver_prof:
                    driver_user_id = driver_prof["user_id"]
                    driver_wallet = await self.wallet_service.get_or_create_wallet(driver_user_id, owner_type="DRIVER")
                    curr_d_bal = self._quantize(Decimal(str(driver_wallet.get("balance", "0.00"))))
                    new_d_bal = curr_d_bal + driver_payout

                    await self.db.update_by_id(
                        "wallets",
                        driver_wallet["id"],
                        {"balance": float(new_d_bal), "updated_at": now_iso},
                    )

                    # Ledger entry: DRIVER_PAYOUT
                    await self.db.insert(
                        "transactions",
                        {
                            "id": str(uuid.uuid4()),
                            "wallet_id": driver_wallet["id"],
                            "user_id": driver_user_id,
                            "type": TransactionType.DRIVER_PAYOUT.value,
                            "amount": float(driver_payout),
                            "currency": "INR",
                            "status": TransactionStatus.COMPLETED.value,
                            "reference_id": delivery_id,
                            "reference_type": "delivery_payout",
                            "description": f"Earnings for completed delivery mission {delivery_id[:8]}",
                            "created_at": now_iso,
                        },
                    )

                    await self.audit.log_event(
                        action="DRIVER_PAYOUT_CREATED",
                        entity_type="wallets",
                        entity_id=driver_wallet["id"],
                        user_id=driver_user_id,
                        new_values={"delivery_id": delivery_id, "amount": float(driver_payout)},
                    )

                    await self.notification.notify_event(
                        user_id=driver_user_id,
                        event_type="DRIVER_PAYOUT",
                        title="Payout Credited",
                        message=f"₹{driver_payout} earnings credited to your wallet for mission {delivery_id[:8]}.",
                        data={"delivery_id": delivery_id, "amount": float(driver_payout)},
                    )

            # 5. Mark delivery as settled
            await self.db.update_by_id(
                "deliveries",
                delivery_id,
                {"is_settled": True, "settled_at": now_iso},
            )

            await self.audit.log_event(
                action="DELIVERY_SETTLED",
                entity_type="deliveries",
                entity_id=delivery_id,
                new_values={
                    "delivery_charge": float(delivery_charge),
                    "platform_fee": float(platform_fee),
                    "driver_payout": float(driver_payout),
                },
            )

            return {
                "delivery_id": delivery_id,
                "status": "SETTLED",
                "delivery_charge": delivery_charge,
                "platform_fee": platform_fee,
                "ngo_total": ngo_total,
                "driver_payout": driver_payout,
                "settled_at": now_iso,
            }

    async def refund_delivery(
        self,
        delivery_id: str,
        reason: str,
        admin_user_id: str,
        amount: Optional[Decimal] = None,
    ) -> PaymentRefundResponse:
        """Processes an administrative refund for a settled delivery, crediting the NGO wallet."""
        delivery = await self.db.get_by_id("deliveries", delivery_id, id_column="id")
        if not delivery:
            raise NotFoundException("Delivery not found.")

        if not delivery.get("is_settled"):
            raise ConflictException("Cannot issue refund for an unsettled delivery mission.")

        # Find captured transactions to calculate refund ceiling
        captured_txs = await self.db.query(
            "transactions",
            params={"reference_id": f"eq.{delivery_id}", "type": f"eq.{TransactionType.DELIVERY_CHARGE.value}"},
        )
        if not captured_txs:
            raise NotFoundException("No captured payment transactions found for this delivery.")

        captured_tx = captured_txs[0]
        wallet_id = captured_tx["wallet_id"]
        ngo_user_id = captured_tx["user_id"]
        captured_amount = self._quantize(Decimal(str(captured_tx["amount"])))

        # Check existing refunds to prevent over-refunding
        existing_refunds = await self.db.query(
            "transactions",
            params={"reference_id": f"eq.{delivery_id}", "type": f"eq.{TransactionType.REFUND.value}"},
        )
        already_refunded = sum(self._quantize(Decimal(str(r["amount"]))) for r in existing_refunds)
        max_refundable = captured_amount - already_refunded

        if max_refundable <= Decimal("0.00"):
            raise ConflictException("Delivery has already been fully refunded.")

        refund_amount = self._quantize(amount) if amount is not None else max_refundable
        if refund_amount <= Decimal("0.00") or refund_amount > max_refundable:
            raise ValidationException(f"Invalid refund amount ₹{refund_amount} (Max refundable: ₹{max_refundable}).")

        now_iso = datetime.now(timezone.utc).isoformat()
        refund_id = str(uuid.uuid4())

        # Credit NGO wallet balance
        ngo_wallet = await self.db.get_by_id("wallets", wallet_id, id_column="id")
        curr_bal = self._quantize(Decimal(str(ngo_wallet.get("balance", "0.00"))))
        new_bal = curr_bal + refund_amount

        await self.db.update_by_id(
            "wallets",
            wallet_id,
            {"balance": float(new_bal), "updated_at": now_iso},
        )

        # Record REFUND transaction
        await self.db.insert(
            "transactions",
            {
                "id": refund_id,
                "wallet_id": wallet_id,
                "user_id": ngo_user_id,
                "type": TransactionType.REFUND.value,
                "amount": float(refund_amount),
                "currency": "INR",
                "status": TransactionStatus.COMPLETED.value,
                "reference_id": delivery_id,
                "reference_type": "refund",
                "description": f"Refund for delivery {delivery_id[:8]}: {reason}",
                "created_at": now_iso,
            },
        )

        await self.audit.log_event(
            action="REFUND_CREATED",
            entity_type="deliveries",
            entity_id=delivery_id,
            user_id=admin_user_id,
            new_values={"amount": float(refund_amount), "reason": reason},
        )

        await self.notification.notify_event(
            user_id=ngo_user_id,
            event_type="REFUND_PROCESSED",
            title="Refund Credited",
            message=f"₹{refund_amount} has been refunded to your wallet for mission {delivery_id[:8]}.",
            data={"delivery_id": delivery_id, "amount": float(refund_amount)},
        )

        return PaymentRefundResponse(
            refund_id=refund_id,
            delivery_id=delivery_id,
            refund_amount=refund_amount,
            wallet_id=wallet_id,
            status="COMPLETED",
            message=f"₹{refund_amount} successfully refunded to NGO wallet.",
        )
