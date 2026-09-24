"""Admin-only demo seed + reset endpoints.

Gated by:
- settings.demo_enabled_safely (i.e. DEMO_MODE=true AND APP_ENV != production)
- require_admin (role-based authorization independent of frontend hiding)
- optional DEMO_RESET_TOKEN configured in env
"""

from __future__ import annotations

from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, Header, HTTPException, status
from app.api.deps import get_supabase_client, require_admin
from app.core.config import settings
from app.db.supabase import SupabaseClient
from app.schemas.auth import ProfileResponse
from app.services.demo_service import DemoService

router = APIRouter(prefix="/admin/demo", tags=["Admin Demo Controls"])


def _check_reset_token(x_demo_reset_token: Optional[str]) -> None:
    if settings.DEMO_RESET_TOKEN:
        if not x_demo_reset_token or x_demo_reset_token != settings.DEMO_RESET_TOKEN:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "code": "DEMO_RESET_TOKEN_REQUIRED",
                    "message": "The server requires a valid X-Demo-Reset-Token header for this operation.",
                },
            )


def get_demo_service(db: SupabaseClient = Depends(get_supabase_client)) -> DemoService:
    return DemoService(db=db)


@router.post(
    "/seed",
    summary="[DEMO_MODE] Seed canonical hackathon scenario",
    description=(
        "Creates or updates the canonical demo dataset (Green Leaf Catering, "
        "Seva Community Kitchen, Arjun Sharma driver, 40 kg donation, active delivery, "
        "wallet reservation, integrity review, and one operational exception). "
        "Only available when DEMO_MODE=true in a non-production APP_ENV. ADMIN only."
    ),
)
async def seed_demo_scenario(
    _admin: ProfileResponse = Depends(require_admin),
    demo_service: DemoService = Depends(get_demo_service),
) -> Dict[str, Any]:
    return await demo_service.seed_demo_scenario()


@router.post(
    "/reset",
    summary="[DEMO_MODE] Reset only demo-owned records",
    description=(
        "Irreversibly removes records tagged with demo_namespace_tag. "
        "Non-demo user data is never touched. "
        "DEMO_MODE + ADMIN + (and optional DEMO_RESET_TOKEN required."
    ),
)
async def reset_demo_data(
    _admin: ProfileResponse = Depends(require_admin),
    demo_service: DemoService = Depends(get_demo_service),
    x_demo_reset_token: Optional[str] = Header(default=None, include_in_schema=False),
    confirm: bool = False,
) -> Dict[str, Any]:
    if not confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "CONFIRMATION_REQUIRED",
                "message": "Pass confirm=true in the query string to proceed with demo data removal.",
            },
        )
    _check_reset_token(x_demo_reset_token)
    return await demo_service.reset_demo_data()


@router.get(
    "/info",
    summary="[DEMO_MODE] Publicly readable demo configuration status",
    description="Returns whether demo mode is enabled and the namespace tag in use.",
)
async def demo_info() -> Dict[str, Any]:
    return {
        "demo_mode_enabled": settings.demo_enabled_safely,
        "app_env": settings.APP_ENV,
        "namespace_tag": settings.DEMO_NAMESPACE_TAG if settings.demo_enabled_safely else None,
        "payment_provider": settings.PAYMENT_PROVIDER,
        "routing_provider": settings.ROUTING_PROVIDER,
        "ai_enabled": settings.AI_ENABLED,
    }
