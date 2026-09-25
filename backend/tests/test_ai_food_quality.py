"""Comprehensive Unit and Integration Tests for Phase 21: AnnaSetu Gemini Food Quality AI Integration."""

import json
from unittest.mock import AsyncMock, MagicMock, patch
import pytest
from pydantic import ValidationError

from app.ai.gemini_provider import GeminiProvider
from app.ai.groq_provider import GroqProvider
from app.ai.schemas import (
    FoodQualityAssessment,
    FreshnessSignal,
    ImageQualitySignal,
    PackagingCondition,
    QualityRecommendation,
)
from app.ai.service import AIService, RateLimiter
from app.utils.exceptions import ForbiddenException, NotFoundException, ValidationException
from tests.conftest import MockSupabaseClient


# =============================================================================
# 1. SCHEMA VALIDATION TESTS
# =============================================================================

def test_food_quality_assessment_schema_valid():
    """Verify FoodQualityAssessment accepts valid visual assessment data."""
    assessment = FoodQualityAssessment(
        donation_id="don-123",
        food_identified="Steamed Rice and Dal",
        visual_quality_score=88,
        freshness_signal=FreshnessSignal.GOOD,
        packaging_condition=PackagingCondition.GOOD,
        image_quality=ImageQualitySignal.GOOD,
        visible_concerns=[],
        risk_flags=[],
        confidence=92,
        recommendation=QualityRecommendation.VISUAL_REVIEW_PASS,
        explanation="Fresh visual appearance in clean covered steel container.",
        disclaimer="Visual AI observation only. Not a food safety certification or shelf-life guarantee.",
        provider="gemini",
    )
    assert assessment.visual_quality_score == 88
    assert assessment.confidence == 92
    assert assessment.recommendation == QualityRecommendation.VISUAL_REVIEW_PASS
    assert "Not a food safety certification" in assessment.disclaimer


def test_food_quality_assessment_score_bounds():
    """Verify visual_quality_score must be between 0 and 100."""
    with pytest.raises(ValidationError):
        FoodQualityAssessment(
            visual_quality_score=150,  # Invalid: > 100
            confidence=90,
        )

    with pytest.raises(ValidationError):
        FoodQualityAssessment(
            visual_quality_score=-5,  # Invalid: < 0
            confidence=90,
        )


# =============================================================================
# 2. GEMINI PROVIDER TESTS
# =============================================================================

@pytest.mark.anyio
async def test_gemini_provider_success():
    """Verify GeminiProvider calls Google GenAI SDK and parses response."""
    mock_response = MagicMock()
    mock_response.text = json.dumps({
        "food_identified": "Mixed Vegetable Curry",
        "visual_quality_score": 85,
        "freshness_signal": "GOOD",
        "packaging_condition": "FAIR",
        "image_quality": "GOOD",
        "visible_concerns": ["Slight condensation on foil cover"],
        "risk_flags": [],
        "confidence": 88,
        "recommendation": "VISUAL_REVIEW_PASS",
        "explanation": "Food looks freshly prepared with intact packaging.",
        "disclaimer": "Visual AI observation only. Not a food safety certification or shelf-life guarantee.",
    })

    provider = GeminiProvider(api_key="test-gemini-key", model="gemini-2.5-flash", enabled=True)
    provider._client = MagicMock()
    provider._client.aio = MagicMock()
    provider._client.aio.models = MagicMock()
    provider._client.aio.models.generate_content = AsyncMock(return_value=mock_response)

    sample_bytes = b"\xff\xd8\xff\xe0\x00\x10JFIF"  # minimal jpeg header
    result = await provider.analyze_food_quality(image_bytes=sample_bytes, mime_type="image/jpeg")

    assert result["food_identified"] == "Mixed Vegetable Curry"
    assert result["visual_quality_score"] == 85
    assert result["freshness_signal"] == "GOOD"
    assert result["recommendation"] == "VISUAL_REVIEW_PASS"
    assert result["provider"] == "gemini"
    assert "Not a food safety certification" in result["disclaimer"]


@pytest.mark.anyio
async def test_gemini_provider_offline_heuristic_fallback():
    """Verify GeminiProvider falls back safely when disabled or unconfigured."""
    provider = GeminiProvider(api_key="", enabled=False)
    sample_bytes = b"sample_bytes"
    result = await provider.analyze_food_quality(image_bytes=sample_bytes, mime_type="image/jpeg")

    assert result["visual_quality_score"] >= 0
    assert result["recommendation"] == "MANUAL_REVIEW"
    assert "Not a food safety certification" in result["disclaimer"]


@pytest.mark.anyio
async def test_gemini_provider_fallback_to_groq():
    """Verify GeminiProvider delegates to fallback provider when Gemini call fails."""
    mock_fallback = MagicMock(spec=GroqProvider)
    mock_fallback.analyze_food_quality = AsyncMock(return_value={
        "food_identified": "Fallback Chapatis",
        "visual_quality_score": 78,
        "freshness_signal": "FAIR",
        "packaging_condition": "GOOD",
        "image_quality": "GOOD",
        "visible_concerns": [],
        "risk_flags": [],
        "confidence": 75,
        "recommendation": "VISUAL_REVIEW_PASS",
        "explanation": "Analyzed by fallback provider.",
        "disclaimer": "Visual AI observation only. Not a food safety certification or shelf-life guarantee.",
        "provider": "groq",
    })

    provider = GeminiProvider(
        api_key="broken-key",
        model="gemini-2.5-flash",
        enabled=True,
        fallback_provider=mock_fallback,
    )
    # Simulate API client failure
    provider._client = MagicMock()
    provider._client.aio.models.generate_content = AsyncMock(side_effect=RuntimeError("Gemini service unavailable"))

    result = await provider.analyze_food_quality(image_bytes=b"bytes", mime_type="image/jpeg")
    assert result["food_identified"] == "Fallback Chapatis"
    assert result["provider"] == "groq"
    assert result["visual_quality_score"] == 78


# =============================================================================
# 3. AI SERVICE & ACCESS CONTROL TESTS
# =============================================================================

@pytest.mark.anyio
async def test_service_analyze_food_quality_authorized_donor_owner():
    """Verify donation donor owner can successfully request AI food quality check."""
    mock_db = MockSupabaseClient()
    mock_provider = MagicMock(spec=GeminiProvider)
    mock_provider.analyze_food_quality = AsyncMock(return_value={
        "food_identified": "Dal Makhani",
        "visual_quality_score": 90,
        "freshness_signal": "GOOD",
        "packaging_condition": "GOOD",
        "image_quality": "GOOD",
        "visible_concerns": [],
        "risk_flags": [],
        "confidence": 95,
        "recommendation": "VISUAL_REVIEW_PASS",
        "explanation": "Properly covered container with fresh appearance.",
        "disclaimer": "Visual AI observation only. Not a food safety certification or shelf-life guarantee.",
        "provider": "gemini",
    })

    service = AIService(db=mock_db, provider=mock_provider)

    donor_id = "donor-user-111"
    donation_id = "donation-222"
    mock_db.donations[donation_id] = {
        "id": donation_id,
        "donor_id": donor_id,
        "raw_description": "20 kg fresh dal makhani",
        "declared_quantity_kg": 20.0,
        "diet_type": "VEGETARIAN",
        "storage_condition": "ambient",
        "packaging_type": "Sealed stainless containers",
        "image_path": "data:image/jpeg;base64,/9j/4AAQSkZJRg==",
        "status": "DRAFT",
    }

    assessment = await service.analyze_donation_food_quality(
        donation_id=donation_id,
        user_id=donor_id,
        user_role="DONOR",
    )

    assert assessment.visual_quality_score == 90
    assert assessment.freshness_signal == FreshnessSignal.GOOD
    assert assessment.recommendation == QualityRecommendation.VISUAL_REVIEW_PASS
    assert assessment.is_cached is False

    # Check updated in DB
    updated = mock_db.donations[donation_id]
    assert "visual_quality_assessment" in updated
    assert updated["visual_quality_assessment"]["visual_quality_score"] == 90


@pytest.mark.anyio
async def test_service_analyze_food_quality_authorized_admin():
    """Verify admin user can request food quality assessment on any donation."""
    mock_db = MockSupabaseClient()
    mock_provider = MagicMock(spec=GeminiProvider)
    mock_provider.analyze_food_quality = AsyncMock(return_value={
        "food_identified": "Vegetable Pulao",
        "visual_quality_score": 82,
        "freshness_signal": "GOOD",
        "packaging_condition": "GOOD",
        "image_quality": "GOOD",
        "visible_concerns": [],
        "risk_flags": [],
        "confidence": 85,
        "recommendation": "VISUAL_REVIEW_PASS",
        "explanation": "Visual check pass.",
        "provider": "gemini",
    })

    service = AIService(db=mock_db, provider=mock_provider)

    admin_id = "admin-user-999"
    donation_id = "donation-333"
    mock_db.donations[donation_id] = {
        "id": donation_id,
        "donor_id": "other-donor-444",
        "raw_description": "15 kg vegetable pulao",
        "declared_quantity_kg": 15.0,
        "image_path": "data:image/jpeg;base64,/9j/4AAQSkZJRg==",
        "status": "POSTED",
    }

    assessment = await service.analyze_donation_food_quality(
        donation_id=donation_id,
        user_id=admin_id,
        user_role="ADMIN",
    )

    assert assessment.visual_quality_score == 82
    assert assessment.donation_id == donation_id


@pytest.mark.anyio
async def test_service_analyze_food_quality_unauthorized_forbidden():
    """Verify unauthorized non-owner/non-admin user is rejected with ForbiddenException."""
    mock_db = MockSupabaseClient()
    service = AIService(db=mock_db, provider=MagicMock())

    donation_id = "donation-555"
    mock_db.donations[donation_id] = {
        "id": donation_id,
        "donor_id": "owner-donor-123",
        "image_path": "data:image/jpeg;base64,/9j/4AAQSkZJRg==",
    }

    with pytest.raises(ForbiddenException):
        await service.analyze_donation_food_quality(
            donation_id=donation_id,
            user_id="intruder-donor-789",
            user_role="DONOR",
        )


@pytest.mark.anyio
async def test_service_caching_duplicate_prevention():
    """Verify repeated assessment on the same unchanged image returns cached result."""
    mock_db = MockSupabaseClient()
    mock_provider = MagicMock(spec=GeminiProvider)
    mock_provider.analyze_food_quality = AsyncMock()

    service = AIService(db=mock_db, provider=mock_provider)

    donor_id = "donor-cache-1"
    donation_id = "donation-cache-1"
    image_ref = "data:image/jpeg;base64,/9j/4AAQSkZJRg=="

    mock_db.donations[donation_id] = {
        "id": donation_id,
        "donor_id": donor_id,
        "image_path": image_ref,
        "visual_quality_assessment": {
            "donation_id": donation_id,
            "food_identified": "Cached Biryani",
            "visual_quality_score": 85,
            "freshness_signal": "GOOD",
            "packaging_condition": "GOOD",
            "image_quality": "GOOD",
            "visible_concerns": [],
            "risk_flags": [],
            "confidence": 90,
            "recommendation": "VISUAL_REVIEW_PASS",
            "explanation": "Cached visual observation.",
            "disclaimer": "Visual AI observation only. Not a food safety certification or shelf-life guarantee.",
            "provider": "gemini",
            "_image_source": image_ref,
        },
    }

    assessment = await service.analyze_donation_food_quality(
        donation_id=donation_id,
        user_id=donor_id,
        user_role="DONOR",
        force_refresh=False,
    )

    assert assessment.is_cached is True
    assert assessment.visual_quality_score == 85
    assert assessment.food_identified == "Cached Biryani"
    # Ensure provider was NOT called
    mock_provider.analyze_food_quality.assert_not_called()


@pytest.mark.anyio
async def test_service_missing_image_validation_error():
    """Verify ValidationException when no image is available."""
    mock_db = MockSupabaseClient()
    service = AIService(db=mock_db, provider=MagicMock())

    donor_id = "donor-no-img"
    donation_id = "donation-no-img"
    mock_db.donations[donation_id] = {
        "id": donation_id,
        "donor_id": donor_id,
        "image_path": None,
    }

    with pytest.raises(ValidationException):
        await service.analyze_donation_food_quality(
            donation_id=donation_id,
            user_id=donor_id,
            user_role="DONOR",
        )
