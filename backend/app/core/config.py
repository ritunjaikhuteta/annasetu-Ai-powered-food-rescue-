"""Application Configuration Settings using Pydantic Settings."""

from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """AnnaSetu Backend Core Settings."""

    PROJECT_NAME: str = "AnnaSetu Backend API"
    VERSION: str = "1.0.0"
    API_V1_PREFIX: str = "/api/v1"
    ENVIRONMENT: str = "development"
    APP_ENV: str = "development"
    PORT: int = 8000

    DEMO_MODE: bool = False
    DEMO_NAMESPACE_TAG: str = "DEMO_SCENARIO_1"
    DEMO_RESET_TOKEN: str = ""

    SUPABASE_URL: str = ""
    SUPABASE_SECRET_KEY: str = ""
    SUPABASE_JWT_SECRET: str = ""

    PAYMENT_PROVIDER: str = "mock"
    RAZORPAY_KEY_ID: str = ""
    RAZORPAY_KEY_SECRET: str = ""
    RAZORPAY_WEBHOOK_SECRET: str = ""
    DEFAULT_PLATFORM_FEE_PERCENT: float = 12.0
    MAX_WALLET_TOPUP_INR: float = 50000.0
    MIN_WALLET_TOPUP_INR: float = 10.0

    AI_PROVIDER: str = "groq"
    AI_FALLBACK_PROVIDER: str = "none"
    AI_ENABLED: bool = True
    GROQ_API_KEY: str = ""
    GROQ_MODEL: str = "llama-3.3-70b-versatile"
    GROQ_VISION_MODEL: str = "llama-3.2-11b-vision-preview"
    GEMINI_API_KEY: str = ""
    GEMINI_MODEL: str = "gemini-2.5-flash"
    AI_REQUEST_TIMEOUT_SECONDS: float = 10.0
    AI_MAX_RETRIES: int = 1

    ROUTING_PROVIDER: str = "haversine"

    FRONTEND_URL: str = "http://localhost:3000"
    ALLOWED_ORIGINS: List[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    def get_cors_origins(self) -> List[str]:
        origins = list(self.ALLOWED_ORIGINS)
        if self.FRONTEND_URL and self.FRONTEND_URL not in origins:
            origins.append(self.FRONTEND_URL)
        return origins

    @property
    def is_production(self) -> bool:
        return self.APP_ENV.lower() in ("production", "prod")

    @property
    def demo_enabled_safely(self) -> bool:
        if self.is_production:
            return False
        return self.DEMO_MODE


settings = Settings()
