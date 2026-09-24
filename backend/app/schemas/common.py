"""Common schemas and enumerations."""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class UserRole(str, Enum):
    DONOR = "DONOR"
    RECEIVER = "RECEIVER"
    DRIVER = "DRIVER"
    ADMIN = "ADMIN"


class VerificationStatus(str, Enum):
    PENDING = "PENDING"
    UNDER_REVIEW = "UNDER_REVIEW"
    VERIFIED = "VERIFIED"
    REJECTED = "REJECTED"


class HealthCheckResponse(BaseModel):
    status: str = Field(default="ok", json_schema_extra={"example": "ok"})
    service: str = Field(default="annasetu-api", json_schema_extra={"example": "annasetu-api"})
    version: str = Field(default="1.0.0", json_schema_extra={"example": "1.0.0"})
    environment: str = Field(default="development", json_schema_extra={"example": "development"})


class VerificationStatusResponse(BaseModel):
    role: UserRole
    verification_status: VerificationStatus
    is_verified: bool
    rejection_reason: Optional[str] = None
