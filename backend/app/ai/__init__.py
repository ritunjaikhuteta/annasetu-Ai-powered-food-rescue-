"""AnnaSetu AI Assistance & Document Intelligence Package."""

from app.ai.groq_provider import GroqProvider
from app.ai.provider import AIProvider
from app.ai.schemas import (
    ConsistencyCheckDetail,
    ConsistencyCheckStatus,
    DocumentConsistencyResponse,
    DocumentExtractionRequest,
    DocumentExtractionResult,
    DocumentReviewResult,
    DonationAIAssistResponse,
    ExplanationResponse,
    ExtractedDocumentFields,
    FoodNormalizationRequest,
    FoodNormalizationResponse,
    NeedAIAssistRequest,
    NeedAIAssistResponse,
)
from app.ai.service import AIService

__all__ = [
    "AIProvider",
    "GroqProvider",
    "AIService",
    "ConsistencyCheckDetail",
    "ConsistencyCheckStatus",
    "DocumentConsistencyResponse",
    "DocumentExtractionRequest",
    "DocumentExtractionResult",
    "DocumentReviewResult",
    "DonationAIAssistResponse",
    "ExplanationResponse",
    "ExtractedDocumentFields",
    "FoodNormalizationRequest",
    "FoodNormalizationResponse",
    "NeedAIAssistRequest",
    "NeedAIAssistResponse",
]
