"""AnnaSetu FastAPI Backend Application Entrypoint."""

import logging
import time
import uuid
from typing import Any, Dict
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.api.routes import (
    allocations,
    deliveries,
    donations,
    donor,
    driver,
    drivers,
    handoffs,
    health,
    integrity,
    matches,
    needs,
    payments,
    pricing,
    profiles,
    receiver,
    subscriptions,
    users,
    wallets,
    ai,
    admin,
    admin_verification,
    admin_operations,
    admin_integrity,
    admin_financial,
    admin_analytics,
    admin_users,
    admin_demo,
)
from app.core.config import settings
from app.schemas.common import HealthCheckResponse
from app.utils.exceptions import AppException
from app.utils.responses import ErrorDetail, ErrorResponse

# Configure root logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] [%(name)s] %(message)s",
)
logger = logging.getLogger("annasetu.main")

# Tags metadata for OpenAPI documentation
tags_metadata = [
    {"name": "Health", "description": "Liveness, readiness, and API metadata."},
    {"name": "Authentication", "description": "Identity, authoritative role, and session verification."},
    {"name": "Profiles", "description": "Self-service profile retrieval and safe field updates."},
    {"name": "Needs", "description": "NGO Hunger Relief Need creation, lifecycle, and requirements."},
    {"name": "Donations", "description": "Surplus Food Donation publishing and lifecycle management."},
    {"name": "Matching", "description": "Deterministic rescue matching engine and priority ranking."},
    {"name": "Allocations", "description": "Atomic food allocation and concurrency-safe commitments."},
    {"name": "Donor", "description": "Donor business profiles and operational data."},
    {"name": "Receiver", "description": "Receiver NGO profiles and operational requirements."},
    {"name": "Driver", "description": "Delivery Partner profiles, vehicle specs, and active status."},
    {"name": "Admin", "description": "Platform administration and verification approval (restricted)."},
]

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Clean, secure backend foundation for AnnaSetu verified food rescue & logistics platform.",
    openapi_tags=tags_metadata,
    docs_url="/docs",
    redoc_url="/redoc",
)

# CORS Middleware (Section 14)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Structured Request Logging Middleware (Section 13)
@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    request.state.request_id = request_id
    start_time = time.perf_counter()

    try:
        response = await call_next(request)
        duration_ms = (time.perf_counter() - start_time) * 1000
        response.headers["X-Request-ID"] = request_id

        logger.info(
            "REQ [%s] %s %s -> %s (%.2fms)",
            request_id[:8],
            request.method,
            request.url.path,
            response.status_code,
            duration_ms,
        )
        return response
    except Exception as exc:
        duration_ms = (time.perf_counter() - start_time) * 1000
        logger.error(
            "REQ [%s] %s %s -> FAILED: %s (%.2fms)",
            request_id[:8],
            request.method,
            request.url.path,
            str(exc),
            duration_ms,
        )
        raise


# Centralized Exception Handlers (Section 12)
@app.exception_handler(AppException)
async def app_exception_handler(request: Request, exc: AppException):
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=ErrorDetail(
                code=exc.error_code,
                message=exc.message,
                details=exc.details,
            )
        ).model_dump(),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = []
    for err in exc.errors():
        loc = " -> ".join(str(l) for l in err.get("loc", []))
        errors.append(f"{loc}: {err.get('msg')}")

    return JSONResponse(
        status_code=422,
        content=ErrorResponse(
            error=ErrorDetail(
                code="VALIDATION_ERROR",
                message="Validation failed for the request payload.",
                details=errors,
            )
        ).model_dump(),
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=ErrorDetail(
                code="HTTP_ERROR",
                message=str(exc.detail),
                details=None,
            )
        ).model_dump(),
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled server exception: %s", exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=ErrorResponse(
            error=ErrorDetail(
                code="INTERNAL_SERVER_ERROR",
                message="An unexpected server error occurred. Please try again later.",
                details=None,
            )
        ).model_dump(),
    )


# Root Health Check (Section 2)
@app.get(
    "/health",
    response_model=HealthCheckResponse,
    tags=["Health"],
    summary="Root Health Check",
    description="Returns standard ok health response required by AnnaSetu Phase 11.",
)
async def root_health() -> Dict[str, Any]:
    return {
        "status": "ok",
        "service": "annasetu-api",
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
    }


# Include API v1 routers (Section 15)
api_v1_prefix = settings.API_V1_PREFIX
app.include_router(health.router, prefix=api_v1_prefix)
app.include_router(users.router, prefix=api_v1_prefix)
app.include_router(profiles.router, prefix=api_v1_prefix)
app.include_router(needs.router, prefix=api_v1_prefix)
app.include_router(donations.router, prefix=api_v1_prefix)
app.include_router(matches.router, prefix=api_v1_prefix)
app.include_router(allocations.router, prefix=api_v1_prefix)
app.include_router(deliveries.router, prefix=api_v1_prefix)
app.include_router(drivers.router, prefix=api_v1_prefix)
app.include_router(donor.router, prefix=api_v1_prefix)
app.include_router(receiver.router, prefix=api_v1_prefix)
app.include_router(driver.router, prefix=api_v1_prefix)
app.include_router(handoffs.router, prefix=api_v1_prefix)
app.include_router(integrity.router, prefix=api_v1_prefix)
app.include_router(pricing.router, prefix=api_v1_prefix)
app.include_router(wallets.router, prefix=api_v1_prefix)
app.include_router(payments.router, prefix=api_v1_prefix)
app.include_router(subscriptions.router, prefix=api_v1_prefix)
app.include_router(ai.router, prefix=api_v1_prefix)
app.include_router(admin.router, prefix=api_v1_prefix)
app.include_router(admin_verification.router, prefix=api_v1_prefix)
app.include_router(admin_operations.router, prefix=api_v1_prefix)
app.include_router(admin_integrity.router, prefix=api_v1_prefix)
app.include_router(admin_financial.router, prefix=api_v1_prefix)
app.include_router(admin_analytics.router, prefix=api_v1_prefix)
app.include_router(admin_users.router, prefix=api_v1_prefix)
app.include_router(admin_demo.router, prefix=api_v1_prefix)

