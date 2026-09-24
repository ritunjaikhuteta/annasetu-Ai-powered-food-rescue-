"""Future Domain Services Stubs for AnnaSetu Architecture.

These modules define domain boundaries and interfaces for upcoming phases:
- need_service: NGO Food Needs management
- donation_service: Surplus Food Donation listing (min 5kg constraint)
- matching_service: Deterministic multi-factor matching
- allocation_service: Allocation caps on donation & need quantities
- delivery_service: Delivery assignments, capacity checks & OTP handoffs
- pricing_service: Deterministic pricing & vehicle rates
- wallet_service: Wallets, escrow & transaction settlements
- verification_service: Document processing & manual review transitions
- impact_service: Carbon offset, meal calculations & metric aggregation
- notification_service: Real-time alerts and webhooks
- ai_service: Contextual AI assistance where genuinely required
"""

from typing import Any, Dict, List, Optional
from app.db.supabase import SupabaseClient


class NeedService:
    """Service stub for NGO Food Needs management."""
    def __init__(self, db: SupabaseClient):
        self.db = db


class DonationService:
    """Service stub for Food Donation lifecycle (enforcing 5kg minimum)."""
    MIN_DONATION_KG = 5.0

    def __init__(self, db: SupabaseClient):
        self.db = db


class MatchingService:
    """Service stub for deterministic food matching."""
    def __init__(self, db: SupabaseClient):
        self.db = db


class AllocationService:
    """Service stub for allocation enforcement."""
    def __init__(self, db: SupabaseClient):
        self.db = db


class DeliveryService:
    """Service stub for delivery mission tracking and vehicle capacity compatibility."""
    def __init__(self, db: SupabaseClient):
        self.db = db


class PricingService:
    """Service stub for deterministic pricing and vehicle rate cards."""
    def __init__(self, db: SupabaseClient):
        self.db = db


class WalletService:
    """Service stub for wallet reservations, escrow, and settlements."""
    def __init__(self, db: SupabaseClient):
        self.db = db


class VerificationService:
    """Service stub for document verification workflow."""
    def __init__(self, db: SupabaseClient):
        self.db = db


class ImpactService:
    """Service stub for environmental and hunger relief impact calculations."""
    def __init__(self, db: SupabaseClient):
        self.db = db


class NotificationService:
    """Service stub for notifications and alerts."""
    def __init__(self, db: SupabaseClient):
        self.db = db


class AIService:
    """Service stub for specialized AI/LLM integrations."""
    def __init__(self, db: SupabaseClient):
        self.db = db
