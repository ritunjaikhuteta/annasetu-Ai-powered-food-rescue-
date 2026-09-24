"""Admin Financial Exceptions and Controlled Adjustments Service."""

from datetime import datetime, timezone
from decimal import Decimal
import logging
from typing import Any, Dict, List, Optional
import uuid
from app.db.supabase import SupabaseClient
from app.schemas.admin_financial import (
    FinancialAdjustRequest,
    FinancialExceptionItem,
    FinancialExceptionType,
    FinancialReviewRequest,
)
from app.services.audit_service import AuditService
from app.utils.exceptions import NotFoundException, ValidationException

logger = logging.getLogger("annasetu.services.admin_financial")


class AdminFinancialService:
    """Service detecting financial exceptions and executing controlled ledger adjustments."""

    def __init__(self, db: SupabaseClient):
        self.db = db
        self.audit = AuditService(db)

    async def list_financial_exceptions(self) -> List[FinancialExceptionItem]:
        """Detects financial anomalies, failed settlements, and invariant violations."""
        exceptions: List[FinancialExceptionItem] = []

        # 1. Failed transactions
        transactions = await self.db.query("transactions")
        for tx in transactions:
            if tx.get("status") == "FAILED":
                exceptions.append(
                    FinancialExceptionItem(
                        id=f"exc-tx-{tx.get('id')}",
                        exception_type=FinancialExceptionType.SETTLEMENT_FAILED.value,
                        severity="HIGH",
                        related_entity_id=tx.get("id", ""),
                        description=f"Transaction {tx.get('type')} of INR {tx.get('amount')} failed.",
                        amount=float(tx.get("amount", 0.0)),
                        created_at=tx.get("created_at", ""),
                    )
                )

        # 2. Stale or unsettled reservations
        reservations = await self.db.query("wallet_reservations")
        for res in reservations:
            if res.get("status") == "RESERVED" and res.get("is_stale"):
                exceptions.append(
                    FinancialExceptionItem(
                        id=f"exc-res-{res.get('id')}",
                        exception_type=FinancialExceptionType.UNSETTLED_RESERVATION.value,
                        severity="MEDIUM",
                        related_entity_id=res.get("id", ""),
                        description=f"Fund reservation for delivery {res.get('delivery_id')} remained unsettled.",
                        amount=float(res.get("amount", 0.0)),
                        created_at=res.get("created_at", ""),
                    )
                )

        # 3. Negative wallet balance checks
        wallets = await self.db.query("wallets")
        for w in wallets:
            bal = float(w.get("balance", 0.0))
            if bal < 0:
                exceptions.append(
                    FinancialExceptionItem(
                        id=f"exc-w-{w.get('id')}",
                        exception_type=FinancialExceptionType.BALANCE_INVARIANT_VIOLATION.value,
                        severity="HIGH",
                        related_entity_id=w.get("id", ""),
                        description=f"Wallet {w.get('id')} has invalid negative balance of INR {bal}.",
                        amount=bal,
                        created_at=w.get("updated_at", ""),
                    )
                )

        return exceptions

    async def review_financial_exception(
        self,
        transaction_id: str,
        admin_id: str,
        payload: FinancialReviewRequest,
    ) -> Dict[str, Any]:
        """Admin marks a financial item reviewed with notes."""
        tx = await self.db.get_by_id("transactions", transaction_id)
        if not tx:
            raise NotFoundException(f"Transaction {transaction_id} not found.")

        now_iso = datetime.now(timezone.utc).isoformat()
        update_data = {
            "review_notes": payload.notes,
            "reviewed_by": admin_id,
            "reviewed_at": now_iso,
        }
        updated = await self.db.update_by_id("transactions", transaction_id, update_data)

        await self.audit.log_event(
            action="FINANCIAL_EXCEPTION_REVIEWED",
            entity_type="transactions",
            entity_id=transaction_id,
            user_id=admin_id,
            new_values=update_data,
        )
        return updated

    async def create_adjustment(
        self,
        admin_id: str,
        payload: FinancialAdjustRequest,
    ) -> Dict[str, Any]:
        """Creates an auditable ADJUSTMENT transaction without modifying historical records in-place."""
        wallet = await self.db.get_by_id("wallets", payload.wallet_id)
        if not wallet:
            raise NotFoundException(f"Wallet {payload.wallet_id} not found.")

        current_balance = Decimal(str(wallet.get("balance", "0.00")))
        adj_amount = Decimal(str(payload.amount))

        if payload.adjustment_type == "CREDIT":
            new_balance = current_balance + adj_amount
        else:
            if current_balance < adj_amount:
                raise ValidationException("Cannot debit more than available wallet balance.")
            new_balance = current_balance - adj_amount

        now_iso = datetime.now(timezone.utc).isoformat()
        tx_id = f"tx-adj-{uuid.uuid4().hex[:10]}"

        # 1. Insert new ADJUSTMENT transaction linking original reference
        tx_record = {
            "id": tx_id,
            "wallet_id": payload.wallet_id,
            "type": "ADJUSTMENT",
            "amount": float(adj_amount),
            "status": "COMPLETED",
            "balance_after": float(new_balance),
            "reference_id": payload.original_reference_id or f"admin-adj-{admin_id}",
            "description": f"Admin Adjustment ({payload.adjustment_type}): {payload.reason}",
            "created_at": now_iso,
            "updated_at": now_iso,
        }
        created_tx = await self.db.insert("transactions", tx_record)

        # 2. Update wallet balance
        await self.db.update_by_id(
            "wallets",
            payload.wallet_id,
            {"balance": float(new_balance), "updated_at": now_iso},
        )

        # 3. Log audit event
        await self.audit.log_event(
            action="FINANCIAL_ADJUSTMENT_CREATED",
            entity_type="wallets",
            entity_id=payload.wallet_id,
            user_id=admin_id,
            new_values={
                "transaction_id": tx_id,
                "adjustment_type": payload.adjustment_type,
                "amount": float(adj_amount),
                "previous_balance": float(current_balance),
                "new_balance": float(new_balance),
                "reason": payload.reason,
            },
        )

        return created_tx
