"""Health and API Metadata endpoints."""

from typing import Any, Dict
from fastapi import APIRouter
from app.core.config import settings
from app.schemas.common import HealthCheckResponse

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    response_model=HealthCheckResponse,
    summary="Application Health Check",
    description="Returns current status, service identifier, and environment.",
)
async def get_health() -> Dict[str, Any]:
    return {
        "status": "ok",
        "service": "annasetu-api",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
    }


@router.get(
    "/info",
    summary="API Service Information",
    description="Returns metadata about AnnaSetu service capabilities and supported endpoints.",
)
async def get_info() -> Dict[str, Any]:
    return {
        "service": "annasetu-api",
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "roles_supported": ["DONOR", "RECEIVER", "DRIVER", "ADMIN"],
        "docs_url": "/docs",
        "openapi_url": "/openapi.json",
    }
