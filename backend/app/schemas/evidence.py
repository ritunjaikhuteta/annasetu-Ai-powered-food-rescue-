"""Handoff Evidence Schemas."""

from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field
from app.schemas.seal import SealStatus


class EvidenceType(str, Enum):
    PACKAGE_PHOTO = "PACKAGE_PHOTO"
    SEAL_PHOTO = "SEAL_PHOTO"
    LOCATION_PROOF = "LOCATION_PROOF"
    OTHER = "OTHER"


class PickupEvidenceRequest(BaseModel):
    package_image: str = Field(..., description="Base64 encoded string or file path for the package photo.")
    seal_image: str = Field(..., description="Base64 encoded string or file path for the tamper seal photo.")
    latitude: Optional[float] = Field(default=None, ge=-90.0, le=90.0)
    longitude: Optional[float] = Field(default=None, ge=-180.0, le=180.0)
    metadata: Optional[Dict[str, Any]] = None


class DeliveryEvidenceRequest(BaseModel):
    package_image: str = Field(..., description="Base64 encoded string or file path for the package photo at delivery.")
    seal_image: str = Field(..., description="Base64 encoded string or file path for the seal photo at delivery.")
    seal_condition: SealStatus = Field(default=SealStatus.INTACT, description="Observed tamper-evident seal condition.")
    latitude: Optional[float] = Field(default=None, ge=-90.0, le=90.0)
    longitude: Optional[float] = Field(default=None, ge=-180.0, le=180.0)
    metadata: Optional[Dict[str, Any]] = None


class HandoffEvidenceResponse(BaseModel):
    id: str
    delivery_id: str
    stop_id: Optional[str] = None
    handoff_id: Optional[str] = None
    evidence_type: EvidenceType
    storage_path: str
    captured_by: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None
    captured_at: Optional[str] = None
