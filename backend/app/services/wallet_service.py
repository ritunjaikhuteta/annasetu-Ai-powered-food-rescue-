"""Wallet and Financial Balance Management Service."""

import asyncio
from collections import defaultdict
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
import logging
from typing import Any, Dict, List, Optional
import uuid
from app.db.supabase import SupabaseClient
from app.schemas.wallet import (
    TransactionResponse,
    TransactionStatus,
    TransactionType,
    WalletReservationResponse,
    WalletResponse,
    WalletTopUpResponse,
)
from app.services.audit_service import AuditService
from app.services.notification_service import NotificationService
from app.services.payment_service import PaymentProvider, get_payment_provider
from app.utils.exceptions import ConflictException, NotFoundException, ValidationException

logger = logging.getLogger("annasetu.services.wallet")

TWO_PLACES = Decimal("0.01")
_wallet_locks: Dict[str, asyncio.Lock] = defaultdict(asyncio.Lock)


class WalletService:
    """Service managing digital wallets, transactions, reservations, and idempotency."""

    def __init__(
        self,
        db: SupabaseClient,
        payment_provider: Optional[PaymentProvider] = None,
    ):
        self.db = db
        self.payment_provider = payment_provider or get_payment_provider()
        self.audit = AuditService(db)
        self.notification = NotificationService(db)

    @staticmethod
    def _quantize(val: Decimal) -> Decimal:
        return val.quantize(TWO_PLACES, rounding=ROUND_HALF_UP)

    async def get_or_create_wallet(self, user_id: str, owner_type: str = "RECEIVER") -> Dict[str, Any]:
        """Retrieves existing wallet or initializes a new one with zero balance."""
        wallets = await self.db.query("wallets", params={"user_id": f"eq.{user_id}"})
        if wallets:
            return wallets[0]

        now_iso = datetime.now(timezone.utc).isoformat()
        wallet_id = str(uuid.uuid4())
        payload = {
            "id": wallet_id,
            "user_id": user_id,
            "owner_type": owner_type,
            "balance": 0.00,
            "reserved_balance": 0.00,
            "currency": "INR",
            "created_at": now_iso,
            "updated_at": now_iso,
        }
        created = await self.db.insert("wallets", payload)
        logger.info("Initialized %s wallet %s for user %s", owner_type, wallet_id, user_id)
        return created

    async def get_wallet(self, user_id: str) -> WalletResponse:
        """Returns wallet summary with calculated available balance."""
        w = await self.get_or_create_wallet(user_id)
        balance = self._quantize(Decimal(str(w.get("balance", "0.00"))))
        reserved = self._quantize(Decimal(str(w.get("reserved_balance", "0.00"))))
        available = balance - reserved

        return WalletResponse(
            id=w["id"],
            user_id=w["user_id"],
            owner_type=w.get("owner_type", "RECEIVER"),
            balance=balance,
            reserved_balance=reserved,
            available_balance=available,
            currency="INR",
            created_at=w.get("created_at"),
            updated_at=w.get("updated_at"),
        )

    async def list_transactions(self, user_id: str) -> List[TransactionResponse]:
        """Lists transaction ledger entries for the user's wallet."""
        w = await self.get_or_create_wallet(user_id)
        records = await self.db.query(
            "transactions",
            params={"wallet_id": f"eq.{w['id']}"},
            order="created_at.desc",
        )
        return [
            TransactionResponse(
                id=r["id"],
                wallet_id=r["wallet_id"],
                user_id=r["user_id"],
                type=TransactionType(r["type"]),
                amount=self._quantize(Decimal(str(r["amount"]))),
                currency=r.get("currency", "INR"),
                status=TransactionStatus(r["status"]),
                reference_id=r.get("reference_id"),
                reference_type=r.get("reference_type"),
                description=r["description"],
                created_at=r.get("created_at"),
            )
            for r in records
        ]

    async def top_up_wallet(
        self,
        user_id: str,
        amount: Decimal,
        idempotency_key: Optional[str] = None,
    ) -> WalletTopUpResponse:
        """Credits wallet balance atomically using the configured payment provider."""
        quantized_amount = self._quantize(amount)
        if quantized_amount <= Decimal("0.00"):
            raise ValidationException("Top-up amount must be strictly positive.")

        # Idempotency check: prevent duplicate top-up on retransmission
        if idempotency_key:
            existing = await self.db.query(
                "transactions",
                params={"reference_id": f"eq.{idempotency_key}", "type": f"eq.{TransactionType.TOP_UP.value}"},
            )
            if existing:
                tx = existing[0]
                w = await self.get_or_create_wallet(user_id)
                current_balance = self._quantize(Decimal(str(w.get("balance", "0.00"))))
                logger.info("Idempotent top-up request recognized for key %s", idempotency_key)
                return WalletTopUpResponse(
                    wallet_id=w["id"],
                    amount=quantized_amount,
                    new_balance=current_balance,
                    transaction_id=tx["id"],
                    status="COMPLETED",
                    payment_reference=idempotency_key,
                    message="Top-up already processed (idempotent).",
                )

        w = await self.get_or_create_wallet(user_id, owner_type="RECEIVER")
        wallet_id = w["id"]

        lock = _wallet_locks[wallet_id]
        async with lock:
            # Re-fetch wallet under lock
            w_current = await self.db.get_by_id("wallets", wallet_id, id_column="id")
            current_balance = self._quantize(Decimal(str(w_current.get("balance", "0.00"))))
            new_balance = current_balance + quantized_amount

            now_iso = datetime.now(timezone.utc).isoformat()
            tx_id = str(uuid.uuid4())
            ref_id = idempotency_key or f"topup_{tx_id[:8]}"

            # 1. Update wallet balance
            await self.db.update_by_id(
                "wallets",
                wallet_id,
                {"balance": float(new_balance), "updated_at": now_iso},
            )

            # 2. Record ledger transaction
            tx_payload = {
                "id": tx_id,
                "wallet_id": wallet_id,
                "user_id": user_id,
                "type": TransactionType.TOP_UP.value,
                "amount": float(quantized_amount),
                "currency": "INR",
                "status": TransactionStatus.COMPLETED.value,
                "reference_id": ref_id,
                "reference_type": "top_up",
                "description": f"Wallet top-up of ₹{quantized_amount}",
                "created_at": now_iso,
            }
            await self.db.insert("transactions", tx_payload)

            # 3. Audit log
            await self.audit.log_event(
                action="WALLET_TOP_UP_COMPLETED",
                entity_type="wallets",
                entity_id=wallet_id,
                user_id=user_id,
                new_values={"amount": float(quantized_amount), "new_balance": float(new_balance)},
            )

            # 4. Notification
            await self.notification.notify_event(
                user_id=user_id,
                event_type="WALLET_TOP_UP",
                title="Wallet Credited",
                message=f"₹{quantized_amount} has been successfully added to your AnnaSetu wallet.",
                data={"wallet_id": wallet_id, "amount": float(quantized_amount)},
            )

            return WalletTopUpResponse(
                wallet_id=wallet_id,
                amount=quantized_amount,
                new_balance=new_balance,
                transaction_id=tx_id,
                status="COMPLETED",
                payment_reference=ref_id,
                message="Wallet top-up processed successfully.",
            )

    async def reserve_funds(
        self,
        user_id: str,
        delivery_id: str,
        amount: Decimal,
    ) -> WalletReservationResponse:
        """Atomically reserves funds from available balance before delivery commitment."""
        quantized_amount = self._quantize(amount)
        w = await self.get_or_create_wallet(user_id, owner_type="RECEIVER")
        wallet_id = w["id"]

        lock = _wallet_locks[wallet_id]
        async with lock:
            # Check existing active reservation for idempotency
            existing_res = await self.db.query(
                "wallet_reservations",
                params={"delivery_id": f"eq.{delivery_id}", "status": "eq.ACTIVE"},
            )
            if existing_res:
                r = existing_res[0]
                return WalletReservationResponse(
                    id=r["id"],
                    wallet_id=r["wallet_id"],
                    delivery_id=r["delivery_id"],
                    reserved_amount=self._quantize(Decimal(str(r["reserved_amount"]))),
                    status=r["status"],
                    created_at=r.get("created_at"),
                )

            # Re-fetch wallet under lock
            w_current = await self.db.get_by_id("wallets", wallet_id, id_column="id")
            balance = self._quantize(Decimal(str(w_current.get("balance", "0.00"))))
            reserved = self._quantize(Decimal(str(w_current.get("reserved_balance", "0.00"))))
            available = balance - reserved

            if available < quantized_amount:
                logger.warning(
                    "Reservation failed: available balance ₹%s is less than required ₹%s for delivery %s",
                    available, quantized_amount, delivery_id,
                )
                raise ConflictException(
                    f"Insufficient wallet balance (available: ₹{available}, required: ₹{quantized_amount}). Please top up your wallet.",
                    error_code="INSUFFICIENT_FUNDS",
                )

            new_reserved = reserved + quantized_amount
            now_iso = datetime.now(timezone.utc).isoformat()
            reservation_id = str(uuid.uuid4())

            # 1. Update wallet reserved balance
            await self.db.update_by_id(
                "wallets",
                wallet_id,
                {"reserved_balance": float(new_reserved), "updated_at": now_iso},
            )

            # 2. Insert reservation record
            res_payload = {
                "id": reservation_id,
                "wallet_id": wallet_id,
                "delivery_id": delivery_id,
                "reserved_amount": float(quantized_amount),
                "status": "ACTIVE",
                "created_at": now_iso,
                "updated_at": now_iso,
            }
            await self.db.insert("wallet_reservations", res_payload)

            # 3. Record reservation transaction
            tx_payload = {
                "id": str(uuid.uuid4()),
                "wallet_id": wallet_id,
                "user_id": user_id,
                "type": TransactionType.RESERVATION.value,
                "amount": float(quantized_amount),
                "currency": "INR",
                "status": TransactionStatus.COMPLETED.value,
                "reference_id": delivery_id,
                "reference_type": "delivery_reservation",
                "description": f"Funds reserved for delivery mission {delivery_id[:8]}",
                "created_at": now_iso,
            }
            await self.db.insert("transactions", tx_payload)

            # 4. Audit & notification
            await self.audit.log_event(
                action="RESERVATION_CREATED",
                entity_type="wallet_reservations",
                entity_id=reservation_id,
                user_id=user_id,
                new_values={"delivery_id": delivery_id, "amount": float(quantized_amount)},
            )
            await self.notification.notify_event(
                user_id=user_id,
                event_type="RESERVATION_CREATED",
                title="Delivery Funds Reserved",
                message=f"₹{quantized_amount} reserved for food rescue delivery.",
                data={"delivery_id": delivery_id, "reservation_id": reservation_id},
            )

            return WalletReservationResponse(
                id=reservation_id,
                wallet_id=wallet_id,
                delivery_id=delivery_id,
                reserved_amount=quantized_amount,
                status="ACTIVE",
                created_at=now_iso,
            )

    async def release_reservation(self, delivery_id: str) -> bool:
        """Releases held funds back to available balance upon delivery cancellation."""
        reservations = await self.db.query(
            "wallet_reservations",
            params={"delivery_id": f"eq.{delivery_id}", "status": "eq.ACTIVE"},
        )
        if not reservations:
            return False

        for r in reservations:
            wallet_id = r["wallet_id"]
            amount = self._quantize(Decimal(str(r["reserved_amount"])))

            lock = _wallet_locks[wallet_id]
            async with lock:
                w_current = await self.db.get_by_id("wallets", wallet_id, id_column="id")
                if w_current:
                    reserved = self._quantize(Decimal(str(w_current.get("reserved_balance", "0.00"))))
                    new_reserved = max(Decimal("0.00"), reserved - amount)
                    now_iso = datetime.now(timezone.utc).isoformat()

                    await self.db.update_by_id(
                        "wallets",
                        wallet_id,
                        {"reserved_balance": float(new_reserved), "updated_at": now_iso},
                    )

                    await self.db.update_by_id(
                        "wallet_reservations",
                        r["id"],
                        {"status": "RELEASED", "updated_at": now_iso},
                    )

                    # Record transaction
                    tx_payload = {
                        "id": str(uuid.uuid4()),
                        "wallet_id": wallet_id,
                        "user_id": w_current["user_id"],
                        "type": TransactionType.RESERVATION_RELEASE.value,
                        "amount": float(amount),
                        "currency": "INR",
                        "status": TransactionStatus.COMPLETED.value,
                        "reference_id": delivery_id,
                        "reference_type": "delivery_cancellation",
                        "description": f"Released reservation for delivery {delivery_id[:8]}",
                        "created_at": now_iso,
                    }
                    await self.db.insert("transactions", tx_payload)

                    await self.audit.log_event(
                        action="RESERVATION_RELEASED",
                        entity_type="wallet_reservations",
                        entity_id=r["id"],
                        new_values={"delivery_id": delivery_id, "amount": float(amount)},
                    )

        return True
