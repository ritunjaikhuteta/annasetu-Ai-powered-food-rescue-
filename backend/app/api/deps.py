"""API Route Dependencies and Service Injections."""

from fastapi import Depends
from app.core.config import settings
from app.core.dependencies import (
    get_auth_service,
    get_current_profile,
    get_current_user,
    require_admin,
    require_donor,
    require_driver,
    require_receiver,
    require_role,
    require_verified_donor,
    require_verified_driver,
    require_verified_receiver,
    require_verified_role,
)
from app.db.supabase import SupabaseClient, get_supabase_client
from app.services.allocation_service import AllocationService
from app.services.auth_service import AuthService
from app.services.donation_service import DonationService
from app.services.donor_service import DonorService
from app.services.driver_service import DriverService
from app.services.matching_service import MatchingService
from app.services.need_service import NeedService
from app.services.profile_service import ProfileService
from app.services.receiver_service import ReceiverService
from app.services.delivery_service import DeliveryService
from app.services.handoff_service import HandoffService
from app.services.integrity_service import IntegrityService
from app.services.pricing_service import PricingService
from app.services.wallet_service import WalletService
from app.services.settlement_service import SettlementService
from app.services.subscription_service import SubscriptionService


def get_profile_service(
    db: SupabaseClient = Depends(get_supabase_client),
) -> ProfileService:
    return ProfileService(db)


def get_donor_service(
    db: SupabaseClient = Depends(get_supabase_client),
) -> DonorService:
    return DonorService(db)


def get_receiver_service(
    db: SupabaseClient = Depends(get_supabase_client),
) -> ReceiverService:
    return ReceiverService(db)


def get_driver_service(
    db: SupabaseClient = Depends(get_supabase_client),
) -> DriverService:
    return DriverService(db)


def get_need_service(
    db: SupabaseClient = Depends(get_supabase_client),
) -> NeedService:
    return NeedService(db)


def get_donation_service(
    db: SupabaseClient = Depends(get_supabase_client),
) -> DonationService:
    return DonationService(db)


def get_matching_service(
    db: SupabaseClient = Depends(get_supabase_client),
) -> MatchingService:
    return MatchingService(db)


def get_allocation_service(
    db: SupabaseClient = Depends(get_supabase_client),
) -> AllocationService:
    return AllocationService(db)


def get_delivery_service(
    db: SupabaseClient = Depends(get_supabase_client),
) -> DeliveryService:
    return DeliveryService(db)


def get_handoff_service(
    db: SupabaseClient = Depends(get_supabase_client),
) -> HandoffService:
    return HandoffService(db)


def get_integrity_service(
    db: SupabaseClient = Depends(get_supabase_client),
) -> IntegrityService:
    return IntegrityService(db)


def get_pricing_service(
    db: SupabaseClient = Depends(get_supabase_client),
) -> PricingService:
    return PricingService(db)


def get_wallet_service(
    db: SupabaseClient = Depends(get_supabase_client),
) -> WalletService:
    return WalletService(db)


def get_settlement_service(
    db: SupabaseClient = Depends(get_supabase_client),
) -> SettlementService:
    return SettlementService(db)


def get_subscription_service(
    db: SupabaseClient = Depends(get_supabase_client),
) -> SubscriptionService:
    return SubscriptionService(db)


def get_ai_service(
    db: SupabaseClient = Depends(get_supabase_client),
) -> "AIService":
    from app.ai.service import AIService
    from app.ai.gemini_provider import GeminiProvider
    from app.ai.groq_provider import GroqProvider

    provider_name = settings.AI_PROVIDER.lower()
    fallback_name = settings.AI_FALLBACK_PROVIDER.lower()

    fallback_provider = None
    if fallback_name == "groq":
        fallback_provider = GroqProvider()
    elif fallback_name == "gemini":
        fallback_provider = GeminiProvider()

    if provider_name == "gemini":
        provider = GeminiProvider(fallback_provider=fallback_provider)
    else:
        provider = GroqProvider()

    return AIService(db=db, provider=provider)


def get_admin_service(
    db: SupabaseClient = Depends(get_supabase_client),
) -> "AdminService":
    from app.services.admin_service import AdminService
    return AdminService(db=db)


def get_admin_verification_service(
    db: SupabaseClient = Depends(get_supabase_client),
) -> "AdminVerificationService":
    from app.services.admin_verification_service import AdminVerificationService
    return AdminVerificationService(db=db)


def get_admin_operations_service(
    db: SupabaseClient = Depends(get_supabase_client),
) -> "AdminOperationsService":
    from app.services.admin_operations_service import AdminOperationsService
    return AdminOperationsService(db=db)


def get_admin_financial_service(
    db: SupabaseClient = Depends(get_supabase_client),
) -> "AdminFinancialService":
    from app.services.admin_financial_service import AdminFinancialService
    return AdminFinancialService(db=db)


def get_admin_analytics_service(
    db: SupabaseClient = Depends(get_supabase_client),
) -> "AdminAnalyticsService":
    from app.services.admin_analytics_service import AdminAnalyticsService
    return AdminAnalyticsService(db=db)

