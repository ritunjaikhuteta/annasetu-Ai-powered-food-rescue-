"""Pydantic Schemas for AI Assistance, Document OCR, and Operational Explanations."""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ConsistencyCheckStatus(str, Enum):
    MATCH = "MATCH"
    MISMATCH = "MISMATCH"
    PARTIAL_MATCH = "PARTIAL_MATCH"
    NOT_CHECKED = "NOT_CHECKED"


class DocumentReviewResult(str, Enum):
    EXTRACTED_SUCCESSFULLY = "EXTRACTED_SUCCESSFULLY"
    EXTRACTION_UNCERTAIN = "EXTRACTION_UNCERTAIN"
    DOCUMENT_MISMATCH = "DOCUMENT_MISMATCH"
    EXPIRED_DOCUMENT = "EXPIRED_DOCUMENT"
    MANUAL_REVIEW_REQUIRED = "MANUAL_REVIEW_REQUIRED"


class ExtractedDocumentFields(BaseModel):
    """Normalized structured candidate fields extracted from verification documents."""
    document_type: Optional[str] = None
    document_number: Optional[str] = None
    holder_name: Optional[str] = None
    organization_name: Optional[str] = None
    vehicle_number: Optional[str] = None
    issue_date: Optional[str] = None
    expiry_date: Optional[str] = None
    issuing_authority: Optional[str] = None
    raw_snippet: Optional[str] = None


class DocumentExtractionRequest(BaseModel):
    document_id: str
    document_type: Optional[str] = None
    ocr_text: Optional[str] = None
    image_url: Optional[str] = None


class DocumentExtractionResult(BaseModel):
    document_id: str
    document_type: str
    fields: ExtractedDocumentFields
    confidence: float = Field(default=0.0, ge=0.0, le=100.0)
    uncertainties: List[str] = Field(default_factory=list)
    method: str = "DETERMINISTIC"  # "DETERMINISTIC", "AI_ASSISTED", "FALLBACK"
    review_status: DocumentReviewResult = DocumentReviewResult.MANUAL_REVIEW_REQUIRED
    stored_in_db: bool = False


class ConsistencyCheckDetail(BaseModel):
    field_name: str
    extracted_value: Optional[str] = None
    profile_value: Optional[str] = None
    status: ConsistencyCheckStatus = ConsistencyCheckStatus.NOT_CHECKED
    reason: str


class DocumentConsistencyResponse(BaseModel):
    document_id: str
    overall_status: ConsistencyCheckStatus
    is_expired: bool = False
    review_recommendation: DocumentReviewResult
    details: List[ConsistencyCheckDetail] = Field(default_factory=list)
    audit_note: str


class FoodNormalizationRequest(BaseModel):
    raw_description: str = Field(..., min_length=1, max_length=500)


class FoodNormalizationResponse(BaseModel):
    raw_description: str
    normalized_description: str
    possible_category: Optional[str] = None
    possible_diet_type: Optional[str] = None
    estimated_quantity_kg: Optional[float] = None
    meal_period: Optional[str] = None
    possible_allergens: List[str] = Field(default_factory=list)
    uncertainties: List[str] = Field(default_factory=list)
    is_ai_generated: bool = False


class DonationAIAssistResponse(BaseModel):
    donation_id: str
    declared_quantity_kg: float
    normalized_description: Optional[str] = None
    category_suggestion: Optional[str] = None
    diet_suggestion: Optional[str] = None
    meal_period_suggestion: Optional[str] = None
    quantity_consistency_signal: str = "NOT_ESTIMATED"  # CONSISTENT, DISCREPANCY, NOT_ESTIMATED
    estimated_quantity_kg: Optional[float] = None
    missing_information_suggestions: List[str] = Field(default_factory=list)
    allergen_suggestions: List[str] = Field(default_factory=list)
    disclaimer: str = "Donor-declared quantity remains authoritative. Suggested values require donor confirmation."


class NeedAIAssistRequest(BaseModel):
    free_text_requirement: Optional[str] = Field(None, max_length=500)


class NeedAIAssistResponse(BaseModel):
    need_id: str
    suggested_meal_period: Optional[str] = None
    suggested_diet_type: Optional[str] = None
    suggested_quantity_kg: Optional[float] = None
    special_requirements_suggestions: List[str] = Field(default_factory=list)
    uncertainties: List[str] = Field(default_factory=list)
    disclaimer: str = "AI suggestions are non-authoritative. Quantities and requirements must be confirmed by the NGO."


class ExplanationResponse(BaseModel):
    entity_id: str
    explanation_type: str
    explanation_text: str
    is_ai_generated: bool = False
    facts: Dict[str, Any] = Field(default_factory=dict)


class FreshnessSignal(str, Enum):
    GOOD = "GOOD"
    FAIR = "FAIR"
    CONCERN = "CONCERN"
    UNKNOWN = "UNKNOWN"


class PackagingCondition(str, Enum):
    GOOD = "GOOD"
    FAIR = "FAIR"
    POOR = "POOR"
    NOT_VISIBLE = "NOT_VISIBLE"


class ImageQualitySignal(str, Enum):
    GOOD = "GOOD"
    FAIR = "FAIR"
    INSUFFICIENT = "INSUFFICIENT"


class QualityRecommendation(str, Enum):
    VISUAL_REVIEW_PASS = "VISUAL_REVIEW_PASS"
    MANUAL_REVIEW = "MANUAL_REVIEW"
    INSUFFICIENT_IMAGE = "INSUFFICIENT_IMAGE"


class FoodQualityAssessment(BaseModel):
    """Structured visual assessment of surplus food image. Non-authoritative."""
    donation_id: Optional[str] = None
    food_identified: Optional[str] = None
    visual_quality_score: int = Field(..., ge=0, le=100, description="Visual Quality Score from 0 to 100")
    freshness_signal: FreshnessSignal = FreshnessSignal.UNKNOWN
    packaging_condition: PackagingCondition = PackagingCondition.NOT_VISIBLE
    image_quality: ImageQualitySignal = ImageQualitySignal.FAIR
    visible_concerns: List[str] = Field(default_factory=list)
    risk_flags: List[str] = Field(default_factory=list)
    confidence: int = Field(..., ge=0, le=100)
    recommendation: QualityRecommendation = QualityRecommendation.MANUAL_REVIEW
    explanation: str = ""
    disclaimer: str = "Visual AI observation only. Not a food safety certification or shelf-life guarantee."
    is_cached: bool = False
    provider: str = "gemini"
    analyzed_at: Optional[str] = None


class FoodQualityCheckRequest(BaseModel):
    image_url: Optional[str] = None
    image_base64: Optional[str] = None
