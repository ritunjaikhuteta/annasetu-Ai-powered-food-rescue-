"""Payment Provider Abstraction and Implementations."""

from abc import ABC, abstractmethod
from decimal import Decimal
import hashlib
import hmac
import logging
import uuid
from typing import Any, Dict, Optional
import httpx
from app.core.config import settings

logger = logging.getLogger("annasetu.services.payment")


class PaymentProvider(ABC):
    """Abstract payment gateway provider."""

    @abstractmethod
    async def create_order(
        self,
        amount: Decimal,
        currency: str,
        receipt: str,
        notes: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Creates an order at the payment gateway."""
        pass

    @abstractmethod
    async def verify_payment(
        self,
        order_id: str,
        payment_id: str,
        signature: str,
    ) -> bool:
        """Verifies payment signature cryptographically."""
        pass

    @abstractmethod
    async def process_refund(
        self,
        payment_reference: str,
        amount: Decimal,
        reason: str,
    ) -> Dict[str, Any]:
        """Initiates a refund via the payment gateway."""
        pass

    @abstractmethod
    async def handle_webhook(
        self,
        payload_bytes: bytes,
        signature: str,
    ) -> Dict[str, Any]:
        """Validates and parses gateway webhook."""
        pass


class MockPaymentProvider(PaymentProvider):
    """Safe simulated payment gateway for demo and hackathon usage without credentials."""

    async def create_order(
        self,
        amount: Decimal,
        currency: str,
        receipt: str,
        notes: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        order_id = f"mock_order_{uuid.uuid4().hex[:12]}"
        logger.info("[MOCK PAYMENT] Created order %s for amount %s %s (Receipt: %s)", order_id, amount, currency, receipt)
        return {
            "order_id": order_id,
            "amount": amount,
            "currency": currency,
            "provider": "mock",
            "status": "created",
            "key_id": "mock_key_public_demo",
        }

    async def verify_payment(
        self,
        order_id: str,
        payment_id: str,
        signature: str,
    ) -> bool:
        # In mock mode, any non-empty mock payment identifier is accepted
        logger.info("[MOCK PAYMENT] Verified payment %s for order %s", payment_id, order_id)
        return bool(order_id and payment_id)

    async def process_refund(
        self,
        payment_reference: str,
        amount: Decimal,
        reason: str,
    ) -> Dict[str, Any]:
        refund_id = f"mock_rfnd_{uuid.uuid4().hex[:12]}"
        logger.info("[MOCK PAYMENT] Processed refund %s of %s for payment %s (Reason: %s)", refund_id, amount, payment_reference, reason)
        return {
            "refund_id": refund_id,
            "amount": amount,
            "status": "processed",
            "payment_reference": payment_reference,
        }

    async def handle_webhook(
        self,
        payload_bytes: bytes,
        signature: str,
    ) -> Dict[str, Any]:
        logger.info("[MOCK PAYMENT] Webhook received (Mock Mode)")
        return {"event": "payment.captured", "status": "simulated"}


class RazorpayPaymentProvider(PaymentProvider):
    """Production Razorpay payment provider with HMAC-SHA256 signature verification."""

    def __init__(
        self,
        key_id: Optional[str] = None,
        key_secret: Optional[str] = None,
        webhook_secret: Optional[str] = None,
    ):
        self.key_id = key_id or settings.RAZORPAY_KEY_ID
        self.key_secret = key_secret or settings.RAZORPAY_KEY_SECRET
        self.webhook_secret = webhook_secret or settings.RAZORPAY_WEBHOOK_SECRET

    async def create_order(
        self,
        amount: Decimal,
        currency: str,
        receipt: str,
        notes: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        if not self.key_id or not self.key_secret:
            raise ValueError("Razorpay credentials not configured.")

        # Razorpay expects amounts in paise (subunits of INR: 1 INR = 100 paise)
        amount_subunits = int(amount * Decimal("100"))
        url = "https://api.razorpay.com/v1/orders"

        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.post(
                url,
                auth=(self.key_id, self.key_secret),
                json={
                    "amount": amount_subunits,
                    "currency": currency,
                    "receipt": receipt,
                    "notes": notes or {},
                },
            )
            if res.status_code in (200, 201):
                data = res.json()
                return {
                    "order_id": data["id"],
                    "amount": amount,
                    "currency": currency,
                    "provider": "razorpay",
                    "status": data.get("status", "created"),
                    "key_id": self.key_id,
                }
            logger.error("Razorpay order creation failed: %s %s", res.status_code, res.text)
            raise RuntimeError(f"Payment provider error: {res.text}")

    async def verify_payment(
        self,
        order_id: str,
        payment_id: str,
        signature: str,
    ) -> bool:
        if not self.key_secret:
            return False
        message = f"{order_id}|{payment_id}"
        expected_signature = hmac.new(
            self.key_secret.encode("utf-8"),
            message.encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        return hmac.compare_digest(expected_signature, signature)

    async def process_refund(
        self,
        payment_reference: str,
        amount: Decimal,
        reason: str,
    ) -> Dict[str, Any]:
        amount_subunits = int(amount * Decimal("100"))
        url = f"https://api.razorpay.com/v1/payments/{payment_reference}/refund"

        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.post(
                url,
                auth=(self.key_id, self.key_secret),
                json={"amount": amount_subunits, "notes": {"reason": reason}},
            )
            if res.status_code in (200, 201):
                data = res.json()
                return {
                    "refund_id": data["id"],
                    "amount": amount,
                    "status": data.get("status", "processed"),
                    "payment_reference": payment_reference,
                }
            logger.error("Razorpay refund failed: %s %s", res.status_code, res.text)
            raise RuntimeError(f"Refund provider error: {res.text}")

    async def handle_webhook(
        self,
        payload_bytes: bytes,
        signature: str,
    ) -> Dict[str, Any]:
        if not self.webhook_secret:
            raise ValueError("Razorpay webhook secret not configured.")
        expected_sig = hmac.new(
            self.webhook_secret.encode("utf-8"),
            payload_bytes,
            hashlib.sha256,
        ).hexdigest()
        if not hmac.compare_digest(expected_sig, signature):
            raise PermissionError("Invalid webhook signature.")
        return {"status": "verified"}


def get_payment_provider() -> PaymentProvider:
    """Factory to load configured payment provider."""
    provider_type = getattr(settings, "PAYMENT_PROVIDER", "mock").lower()
    if provider_type == "razorpay" and settings.RAZORPAY_KEY_ID:
        return RazorpayPaymentProvider()
    return MockPaymentProvider()
