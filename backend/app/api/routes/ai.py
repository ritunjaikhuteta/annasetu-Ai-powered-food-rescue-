"""AnnaSetu AI Assistance, OCR & Document Intelligence Endpoints."""

from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from app.ai.schemas import (
    DocumentConsistencyResponse,
    DocumentExtractionRequest,
    DocumentExtractionResult,
    DonationAIAssistResponse,
    ExplanationResponse,
    FoodNormalizationRequest,
    FoodNormalizationResponse,
    NeedAIAssistRequest,
    NeedAIAssistResponse,
)
from app.ai.service import AIService
from app.api.deps import get_ai_service, get_current_profile
from app.schemas.auth import ProfileResponse

router = APIRouter(tags=["AI Assistance & Document Intelligence"])


@router.post(
    "/ai/normalize-food",
    response_model=FoodNormalizationResponse,
    summary="Normalize Food Description",
    description="Normalizes free-text food descriptions into candidate structured fields using deterministic parsing first, with AI assistance fallback.",
)
async def normalize_food_description(
    payload: FoodNormalizationRequest,
    current_profile: ProfileResponse = Depends(get_current_profile),
    ai_service: AIService = Depends(get_ai_service),
) -> FoodNormalizationResponse:
    return await ai_service.normalize_food_description(
        raw_description=payload.raw_description,
        user_id=current_profile.id,
    )


@router.post(
    "/donations/{donation_id}/ai-assist",
    response_model=DonationAIAssistResponse,
    summary="AI Assistance for Donation",
    description="Provides suggestions for category, diet, meal period, and allergen notes. Donor-declared quantity remains authoritative.",
)
async def assist_donation(
    donation_id: str,
    current_profile: ProfileResponse = Depends(get_current_profile),
    ai_service: AIService = Depends(get_ai_service),
) -> DonationAIAssistResponse:
    return await ai_service.assist_donation(
        donation_id=donation_id,
        user_id=current_profile.id,
    )


@router.post(
    "/needs/{need_id}/ai-assist",
    response_model=NeedAIAssistResponse,
    summary="AI Assistance for Need",
    description="Provides candidate suggestions from free-text need descriptions. Must be explicitly confirmed by NGO receiver.",
)
async def assist_need(
    need_id: str,
    payload: Optional[NeedAIAssistRequest] = None,
    current_profile: ProfileResponse = Depends(get_current_profile),
    ai_service: AIService = Depends(get_ai_service),
) -> NeedAIAssistResponse:
    free_text = payload.free_text_requirement if payload else None
    return await ai_service.assist_need(
        need_id=need_id,
        user_id=current_profile.id,
        free_text_requirement=free_text,
    )


@router.get(
    "/matches/{match_id}/explanation",
    response_model=ExplanationResponse,
    summary="Human-Readable Match Explanation",
    description="Generates transparent natural language explanation of deterministic priority breakdown. Algorithm score is authoritative and immutable.",
)
async def get_match_explanation(
    match_id: str,
    current_profile: ProfileResponse = Depends(get_current_profile),
    ai_service: AIService = Depends(get_ai_service),
) -> ExplanationResponse:
    return await ai_service.get_match_explanation(
        match_id=match_id,
        user_id=current_profile.id,
    )


@router.get(
    "/deliveries/{delivery_id}/explanation",
    response_model=ExplanationResponse,
    summary="Delivery Status Operational Explanation",
    description="Generates concise human-readable explanation based strictly on authoritative delivery state and stop progress.",
)
async def get_delivery_explanation(
    delivery_id: str,
    current_profile: ProfileResponse = Depends(get_current_profile),
    ai_service: AIService = Depends(get_ai_service),
) -> ExplanationResponse:
    return await ai_service.get_delivery_explanation(
        delivery_id=delivery_id,
        user_id=current_profile.id,
    )


@router.post(
    "/documents/{document_id}/process-ocr",
    response_model=DocumentExtractionResult,
    summary="Process Document OCR and Extraction",
    description="Extracts candidate fields from verification document text/image. Extracted fields are stored in verification_documents.extracted_data.",
)
async def process_document_ocr(
    document_id: str,
    payload: Optional[DocumentExtractionRequest] = None,
    current_profile: ProfileResponse = Depends(get_current_profile),
    ai_service: AIService = Depends(get_ai_service),
) -> DocumentExtractionResult:
    raw_ocr = payload.ocr_text if payload else None
    hint = payload.document_type if payload else None
    return await ai_service.process_verification_document(
        document_id=document_id,
        user_id=current_profile.id,
        raw_ocr_text=raw_ocr,
        doc_type_hint=hint,
    )


@router.get(
    "/documents/{document_id}/consistency-check",
    response_model=DocumentConsistencyResponse,
    summary="Check Document Consistency",
    description="Performs deterministic consistency checks between extracted document fields and user/entity profiles. Sets recommendation for manual review.",
)
async def check_document_consistency(
    document_id: str,
    current_profile: ProfileResponse = Depends(get_current_profile),
    ai_service: AIService = Depends(get_ai_service),
) -> DocumentConsistencyResponse:
    return await ai_service.check_document_consistency(
        document_id=document_id,
        user_id=current_profile.id,
    )


@router.get(
    "/impact/{entity_id}/explanation",
    response_model=ExplanationResponse,
    summary="Impact Metric Explanation",
    description="Explains environmental and social impact metrics grounded solely in recorded figures and deterministic factors.",
)
async def get_impact_explanation(
    entity_id: str,
    donation_id: Optional[str] = Query(default=None, description="Optional donation ID for specific impact."),
    current_profile: ProfileResponse = Depends(get_current_profile),
    ai_service: AIService = Depends(get_ai_service),
) -> ExplanationResponse:
    return await ai_service.get_impact_explanation(
        user_id=current_profile.id,
        donation_id=donation_id,
    )
