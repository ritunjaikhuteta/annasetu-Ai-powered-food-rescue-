"""Secure Handoff OTP Service."""

from datetime import datetime, timedelta, timezone
import hashlib
import hmac
import logging
import secrets
from typing import Any, Dict, Optional, Tuple
from app.core.config import settings

logger = logging.getLogger("annasetu.services.otp")


class OTPService:
    """Cryptographically secure OTP generation, hashing, and timing-safe verification."""

    def __init__(
        self,
        otp_length: int = 6,
        expiry_minutes: int = 10,
        max_attempts: int = 5,
        secret_salt: Optional[str] = None,
    ):
        self.otp_length = otp_length
        self.expiry_minutes = expiry_minutes
        self.max_attempts = max_attempts
        self.secret_salt = secret_salt or settings.SUPABASE_JWT_SECRET or "annasetu-secure-otp-salt"

    def generate_otp(self) -> Tuple[str, str, datetime]:
        """Generates a secure numeric OTP, its cryptographic hash, and its expiration time.
        
        Returns:
            (plaintext_otp, otp_hash, expires_at_datetime)
        """
        # Cryptographically secure random numeric OTP
        plaintext_otp = "".join(secrets.choice("0123456789") for _ in range(self.otp_length))
        otp_hash = self.hash_otp(plaintext_otp)
        expires_at = datetime.now(timezone.utc) + timedelta(minutes=self.expiry_minutes)

        # Log event without exposing plaintext OTP
        logger.info("Generated %d-digit handoff OTP with %d min expiry", self.otp_length, self.expiry_minutes)
        return plaintext_otp, otp_hash, expires_at

    def hash_otp(self, raw_otp: str) -> str:
        """Computes SHA-256 HMAC hash of the OTP using the server secret salt."""
        return hmac.new(
            self.secret_salt.encode("utf-8"),
            raw_otp.strip().encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()

    def verify_otp(
        self,
        candidate_otp: str,
        stored_hash: str,
        expires_at_iso: str,
        current_attempts: int,
    ) -> Dict[str, Any]:
        """Verifies candidate OTP in constant time.
        
        Returns:
            {
                "is_valid": bool,
                "is_expired": bool,
                "attempts_exceeded": bool,
                "new_attempts": int
            }
        """
        now = datetime.now(timezone.utc)
        expires_at = datetime.fromisoformat(expires_at_iso.replace("Z", "+00:00"))
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)

        new_attempts = current_attempts + 1

        if now > expires_at:
            logger.info("OTP verification failed: expired")
            return {
                "is_valid": False,
                "is_expired": True,
                "attempts_exceeded": new_attempts >= self.max_attempts,
                "new_attempts": new_attempts,
            }

        if new_attempts > self.max_attempts:
            logger.info("OTP verification failed: maximum attempts exceeded")
            return {
                "is_valid": False,
                "is_expired": False,
                "attempts_exceeded": True,
                "new_attempts": new_attempts,
            }

        candidate_hash = self.hash_otp(candidate_otp)
        is_match = hmac.compare_digest(candidate_hash, stored_hash)

        if not is_match:
            logger.info("OTP verification failed: mismatch (attempt %d/%d)", new_attempts, self.max_attempts)
            return {
                "is_valid": False,
                "is_expired": False,
                "attempts_exceeded": new_attempts >= self.max_attempts,
                "new_attempts": new_attempts,
            }

        logger.info("OTP verification successful")
        return {
            "is_valid": True,
            "is_expired": False,
            "attempts_exceeded": False,
            "new_attempts": new_attempts,
        }
