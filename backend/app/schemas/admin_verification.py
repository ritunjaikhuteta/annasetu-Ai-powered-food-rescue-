"""Admin Verification Queue Schemas."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class VerificationItemResponse(BaseModel):
    id: str
    user_id: str
    role: str
    verification_type: str
    status: str
    created_at: str
    submitted_documents_count: int
    user_full_name: Optional[str] = None
    organization_or_business: Optional[str] = None


class VerificationDetailResponse(BaseModel):
    id: str
    user_id: str
    role: str
    verification_type: str
    status: str
    created_at: str
    verified_at: Optional[str] = None
    verified_by: Optional[str] = None
    rejection_reason: Optional[str] = None
    user_profile: Dict[str, Any] = Field(default_factory=dict)
    role_profile: Dict[str, Any] = Field(default_factory=dict)
    documents: List[Dict[str, Any]] = Field(default_factory=list)


class VerificationApproveRequest(BaseModel):
    review_notes: Optional[str] = None


class VerificationRejectRequest(BaseModel):
    rejection_reason: str = Field(..., min_length=3, max_length=500)


class VerificationRequestReviewRequest(BaseModel):
    review_notes: str = Field(..., min_length=3, max_length=500)
