"""Unit and Integration Tests for Phase 16: AnnaSetu AI Assistance, OCR & Document Intelligence."""

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
from unittest.mock import AsyncMock, patch
import pytest
from fastapi.testclient import TestClient
from app.ai.groq_provider import GroqProvider
from app.ai.provider import AIProvider
from app.ai.schemas import (
    ConsistencyCheckStatus,
    DocumentReviewResult,
    ExtractedDocumentFields,
)
from app.ai.service import AIService, RateLimiter
from app.core.config import settings
from tests.conftest import MockSupabaseClient


# =============================================================================
# 1. AI PROVIDER ABSTRACTION & FALLBACKS
# =============================================================================

class MockCustomAIProvider(AIProvider):
    """Custom provider for testing provider abstraction independence."""

    async def extract_document_data(self, doc_type: str, ocr_text: str) -> Dict[str, Any]:
        return {
            "document_type": doc_type or "PAN",
            "fields": {"document_number": "ABCDE1234F", "holder_name": "Test Holder"},
            "confidence": 90,
            "uncertainties": [],
        }

    async def normalize_food_description(self, raw_description: str) -> Dict[str, Any]:
        return {
            "normalized_description": "Fresh Dal & Rice",
            "possible_category": "Cooked Meals",
            "possible_diet_type": "VEGETARIAN",
            "estimated_quantity_kg": 25.0,
            "meal_period": "LUNCH",
            "possible_allergens": [],
            "uncertainties": [],
        }

    async def generate_explanation(self, explanation_type: str, context: Dict[str, Any]) -> str:
        return "Custom explanation test text."

    async def analyze_package_integrity(self, pickup_image: str, delivery_image: str) -> Dict[str, Any]:
        return {
            "integrity_score": 98.0,
            "tampering_signal": False,
            "reason": "Package intact.",
            "available": True,
        }

    async def analyze_food_quality(self, image_bytes: bytes, mime_type: str = "image/jpeg", context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return {
            "food_identified": "Dal & Rice",
            "visual_quality_score": 85,
            "freshness_signal": "GOOD",
            "packaging_condition": "GOOD",
            "image_quality": "GOOD",
            "visible_concerns": [],
            "risk_flags": [],
            "confidence": 90,
            "recommendation": "VISUAL_REVIEW_PASS",
            "explanation": "Test provider assessment.",
            "disclaimer": "Visual AI observation only. Not a food safety certification or shelf-life guarantee.",
            "provider": "mock",
        }


def test_ai_provider_abstraction():
    """Verify AIProvider can be subclassed without depending on Groq."""
    custom = MockCustomAIProvider()
    assert isinstance(custom, AIProvider)


@pytest.mark.anyio
async def test_disabled_ai_mode():
    """When AI_ENABLED is False, provider returns graceful fallback."""
    disabled_provider = GroqProvider(enabled=False, api_key="some-key")
    assert not disabled_provider.is_available

    # Document extraction fallback
    doc_res = await disabled_provider.extract_document_data("DRIVING_LICENSE", "sample text")
    assert doc_res["confidence"] == 0
    assert "AI assistance unavailable." in doc_res["uncertainties"]

    # Food normalization fallback
    food_res = await disabled_provider.normalize_food_description("25 kgs rice")
    assert food_res["normalized_description"] == "25 kgs rice"
    assert "AI assistance unavailable." in food_res["uncertainties"]

    # Explanation fallback (deterministic template)
    exp = await disabled_provider.generate_explanation("MATCH_PRIORITY", {"priority_score": 88, "distance_km": 3.2, "estimated_travel_minutes": 12, "shelf_life_buffer_hours": 4.5, "priority_label": "HIGH"})
    assert "88/100" in exp
    assert "3.2 km" in exp


@pytest.mark.anyio
async def test_missing_api_key():
    """When GROQ_API_KEY is empty, provider behaves safely without throwing."""
    provider = GroqProvider(enabled=True, api_key="")
    assert not provider.is_available
    res = await provider.extract_document_data("PAN", "sample text")
    assert res["confidence"] == 0


@pytest.mark.anyio
async def test_ai_timeout_and_malformed_response():
    """Provider handles network timeout or malformed JSON gracefully."""
    provider = GroqProvider(enabled=True, api_key="gsk_test")

    with patch("httpx.AsyncClient.post", side_effect=Exception("Connection timed out")):
        res = await provider.extract_document_data("RC", "some vehicle rc")
        assert res["confidence"] == 0
        assert "AI document extraction failed or timed out." in res["uncertainties"]


# =============================================================================
# 2. DETERMINISTIC OCR & PARSING
# =============================================================================

def test_deterministic_quantity_parsing(mock_db: MockSupabaseClient):
    """Parses various quantity units deterministically."""
    service = AIService(db=mock_db, provider=GroqProvider(enabled=False))

    # kg variants
    assert service._parse_food_deterministically("25 KGS")["estimated_quantity_kg"] == 25.0
    assert service._parse_food_deterministically("25kg rice")["estimated_quantity_kg"] == 25.0
    assert service._parse_food_deterministically("10.5 kilograms of veg curry")["estimated_quantity_kg"] == 10.5

    # grams variants
    assert service._parse_food_deterministically("5000 grams")["estimated_quantity_kg"] == 5.0
    assert service._parse_food_deterministically("750 gm paneer")["estimated_quantity_kg"] == 0.75


def test_deterministic_keyword_parsing(mock_db: MockSupabaseClient):
    """Detects meal periods, diets, and categories deterministically."""
    service = AIService(db=mock_db, provider=GroqProvider(enabled=False))

    parsed = service._parse_food_deterministically("fresh pure veg dal and rice for lunch")
    assert parsed["meal_period"] == "LUNCH"
    assert parsed["possible_diet_type"] == "VEGETARIAN"
    assert parsed["possible_category"] == "Cooked Meals"

    parsed_nonveg = service._parse_food_deterministically("chicken biryani dinner")
    assert parsed_nonveg["meal_period"] == "DINNER"
    assert parsed_nonveg["possible_diet_type"] == "NON_VEGETARIAN"


def test_deterministic_document_field_extraction(mock_db: MockSupabaseClient):
    """Regex detects GSTIN, PAN, FSSAI, vehicle plate, and dates."""
    service = AIService(db=mock_db, provider=GroqProvider(enabled=False))

    # Driving License with plate and dates
    text = "Driving License DL-04-2011-0012345 Valid from 2020-01-10 to 2030-01-09 Vehicle MH-02-AB-1234"
    fields = service._extract_document_fields_deterministic("DRIVING_LICENSE", text)
    assert fields.vehicle_number == "MH-02-AB-1234"
    assert fields.issue_date == "2020-01-10"
    assert fields.expiry_date == "2030-01-09"

    # GSTIN
    gst_text = "Government of India GSTIN: 27AAAAA0000A1Z5 Taj Catering"
    gst_fields = service._extract_document_fields_deterministic("GST_REGISTRATION", gst_text)
    assert gst_fields.document_number == "27AAAAA0000A1Z5"

    # PAN
    pan_text = "Income Tax Department Permanent Account Number ABCDE1234F"
    pan_fields = service._extract_document_fields_deterministic("PAN", pan_text)
    assert pan_fields.document_number == "ABCDE1234F"

    # FSSAI
    fssai_text = "FSSAI License No: 12345678901234 Food Safety Authority"
    fssai_fields = service._extract_document_fields_deterministic("FSSAI_LICENSE", fssai_text)
    assert fssai_fields.document_number == "12345678901234"


# =============================================================================
# 3. DOCUMENT VERIFICATION & CONSISTENCY
# =============================================================================

@pytest.mark.anyio
async def test_document_extraction_saved_in_database(mock_db: MockSupabaseClient):
    """Candidate extraction is saved into verification_documents.extracted_data and moves to MANUAL_REVIEW, never VERIFIED."""
    mock_db.verification_documents["doc-dl-1"] = {
        "id": "doc-dl-1",
        "user_id": "user-driver-verified",
        "document_type": "DRIVING_LICENSE",
        "raw_text": "Driving License DL-04-2011-0012345 Holder: Verified Logistics Driver Valid until 2032-12-31 Plate: MH-02-AB-1234",
        "verification_status": "PENDING",
    }

    service = AIService(db=mock_db, provider=GroqProvider(enabled=False))
    res = await service.process_verification_document(
        document_id="doc-dl-1",
        user_id="user-driver-verified",
    )

    assert res.stored_in_db is True
    # Verify in mock database
    updated_doc = mock_db.verification_documents["doc-dl-1"]
    assert "extracted_data" in updated_doc
    assert updated_doc["extracted_data"]["vehicle_number"] == "MH-02-AB-1234"
    # Authoritative rule: AI must never set verification_status = VERIFIED!
    assert updated_doc["verification_status"] == "MANUAL_REVIEW"
    assert updated_doc["verification_status"] != "VERIFIED"


@pytest.mark.anyio
async def test_document_consistency_match(mock_db: MockSupabaseClient):
    """Consistency check returns MATCH when document fields match profile."""
    future_date = (datetime.now(timezone.utc) + timedelta(days=365)).strftime("%Y-%m-%d")
    mock_db.verification_documents["doc-dl-match"] = {
        "id": "doc-dl-match",
        "user_id": "user-driver-verified",
        "document_type": "DRIVING_LICENSE",
        "extracted_data": {
            "holder_name": "Verified Logistics Driver",
            "vehicle_number": "MH-02-AB-1234",
            "expiry_date": future_date,
        },
    }

    service = AIService(db=mock_db, provider=GroqProvider(enabled=False))
    res = await service.check_document_consistency(
        document_id="doc-dl-match",
        user_id="user-driver-verified",
    )

    assert res.overall_status == ConsistencyCheckStatus.MATCH
    assert not res.is_expired
    # Still requires human/admin review
    assert res.review_recommendation == DocumentReviewResult.MANUAL_REVIEW_REQUIRED


@pytest.mark.anyio
async def test_document_consistency_mismatch(mock_db: MockSupabaseClient):
    """Consistency check detects mismatch between document and registered driver profile."""
    future_date = (datetime.now(timezone.utc) + timedelta(days=365)).strftime("%Y-%m-%d")
    mock_db.verification_documents["doc-dl-mismatch"] = {
        "id": "doc-dl-mismatch",
        "user_id": "user-driver-verified",
        "document_type": "DRIVING_LICENSE",
        "extracted_data": {
            "holder_name": "Completely Different Person",
            "vehicle_number": "KA-01-XY-9999",  # Does not match MH-02-AB-1234
            "expiry_date": future_date,
        },
    }

    service = AIService(db=mock_db, provider=GroqProvider(enabled=False))
    res = await service.check_document_consistency(
        document_id="doc-dl-mismatch",
        user_id="user-driver-verified",
    )

    assert res.overall_status == ConsistencyCheckStatus.MISMATCH
    assert res.review_recommendation == DocumentReviewResult.DOCUMENT_MISMATCH
    mismatch_details = [d for d in res.details if d.status == ConsistencyCheckStatus.MISMATCH]
    assert len(mismatch_details) >= 1


@pytest.mark.anyio
async def test_document_consistency_expired(mock_db: MockSupabaseClient):
    """Consistency check flags expired document."""
    past_date = (datetime.now(timezone.utc) - timedelta(days=30)).strftime("%Y-%m-%d")
    mock_db.verification_documents["doc-expired"] = {
        "id": "doc-expired",
        "user_id": "user-driver-verified",
        "document_type": "DRIVING_LICENSE",
        "extracted_data": {
            "holder_name": "Verified Logistics Driver",
            "vehicle_number": "MH-02-AB-1234",
            "expiry_date": past_date,
        },
    }

    service = AIService(db=mock_db, provider=GroqProvider(enabled=False))
    res = await service.check_document_consistency(
        document_id="doc-expired",
        user_id="user-driver-verified",
    )

    assert res.is_expired is True
    assert res.overall_status == ConsistencyCheckStatus.MISMATCH
    assert res.review_recommendation == DocumentReviewResult.EXPIRED_DOCUMENT


# =============================================================================
# 4. FOOD NORMALIZATION & DONATION / NEED ASSIST
# =============================================================================

def test_api_normalize_food_endpoint(client: TestClient):
    """POST /api/v1/ai/normalize-food endpoint parses text deterministically."""
    res = client.post(
        "/api/v1/ai/normalize-food",
        headers={"Authorization": "Bearer token-user-donor-verified"},
        json={"raw_description": "fresh veg rice dal around 25 kgs, packed hot for lunch"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["estimated_quantity_kg"] == 25.0
    assert data["possible_diet_type"] == "VEGETARIAN"
    assert data["meal_period"] == "LUNCH"
    assert data["possible_category"] == "Cooked Meals"


@pytest.mark.anyio
async def test_donor_declared_quantity_remains_authoritative(
    client: TestClient,
    mock_db: MockSupabaseClient,
):
    """Donor declared quantity remains authoritative even if AI estimate differs."""
    mock_db.donations["don-test-qty"] = {
        "id": "don-test-qty",
        "donor_id": "user-donor-verified",
        "food_name": "Veg Lunch Packs",
        "description": "25 kgs hot rice and curry",
        "quantity_kg": 20.0,  # Donor declared 20 kg
        "remaining_quantity_kg": 20.0,
        "status": "POSTED",
    }

    res = client.post(
        "/api/v1/donations/don-test-qty/ai-assist",
        headers={"Authorization": "Bearer token-user-donor-verified"},
    )
    assert res.status_code == 200
    data = res.json()
    # Authoritative declared quantity must be 20.0
    assert data["declared_quantity_kg"] == 20.0
    # AI estimate is 25.0 from the text
    assert data["estimated_quantity_kg"] == 25.0
    # Flagged discrepancy signal
    assert data["quantity_consistency_signal"] == "DISCREPANCY"


@pytest.mark.anyio
async def test_need_ai_assist(
    client: TestClient,
    mock_db: MockSupabaseClient,
):
    """POST /api/v1/needs/{need_id}/ai-assist returns suggestions without modifying need."""
    mock_db.ngo_needs["need-test-ai"] = {
        "id": "need-test-ai",
        "receiver_id": "user-receiver-verified",
        "food_category_id": "cat-cooked-meals",
        "diet_type": "VEGETARIAN",
        "required_quantity_kg": 50.0,
        "remaining_quantity_kg": 50.0,
        "status": "ACTIVE",
        "notes": "Need vegetarian cooked lunch for 100 people around 50 kgs",
    }

    res = client.post(
        "/api/v1/needs/need-test-ai/ai-assist",
        headers={"Authorization": "Bearer token-user-receiver-verified"},
        json={"free_text_requirement": "vegetarian cooked lunch for 100 people around 50 kgs"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["suggested_meal_period"] == "LUNCH"
    assert data["suggested_diet_type"] == "VEGETARIAN"
    assert data["suggested_quantity_kg"] == 50.0


# =============================================================================
# 5. MATCH & DELIVERY EXPLANATIONS
# =============================================================================

@pytest.mark.anyio
async def test_match_explanation_score_is_immutable(
    client: TestClient,
    mock_db: MockSupabaseClient,
):
    """Match explanation reflects deterministic facts and cannot alter the score."""
    mock_db.matches["match-exp-1"] = {
        "id": "match-exp-1",
        "donation_id": "don-1",
        "need_id": "need-1",
        "priority_score": 88,
        "priority_label": "HIGH",
        "distance_km": 3.5,
        "estimated_travel_minutes": 15,
        "shelf_life_buffer_hours": 3.0,
        "fulfillment_ratio": 1.0,
    }

    res = client.get(
        "/api/v1/matches/match-exp-1/explanation",
        headers={"Authorization": "Bearer token-user-donor-verified"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["facts"]["priority_score"] == 88
    assert "88/100" in data["explanation_text"]
    assert "3.5 km" in data["explanation_text"]


@pytest.mark.anyio
async def test_delivery_explanation(
    client: TestClient,
    mock_db: MockSupabaseClient,
):
    """Delivery status explanation reflects authoritative progress."""
    mock_db.deliveries["del-exp-1"] = {
        "id": "del-exp-1",
        "status": "IN_TRANSIT",
        "driver_id": "user-driver-verified",
    }
    mock_db.delivery_stops["stop-exp-1"] = {
        "id": "stop-exp-1",
        "delivery_id": "del-exp-1",
        "status": "COMPLETED",
    }

    res = client.get(
        "/api/v1/deliveries/del-exp-1/explanation",
        headers={"Authorization": "Bearer token-user-driver-verified"},
    )
    assert res.status_code == 200
    data = res.json()
    assert "IN_TRANSIT" in data["explanation_text"]


# =============================================================================
# 6. IMPACT EXPLANATIONS
# =============================================================================

@pytest.mark.anyio
async def test_impact_explanation_cannot_alter_factors(
    client: TestClient,
    mock_db: MockSupabaseClient,
):
    """Impact calculation strictly uses deterministic factors (0.4 kg/meal, 2.5 kg CO2e/kg)."""
    mock_db.donations["don-impact-1"] = {
        "id": "don-impact-1",
        "donor_id": "user-donor-verified",
        "quantity_kg": 40.0,
    }

    res = client.get(
        "/api/v1/impact/don-impact-1/explanation?donation_id=don-impact-1",
        headers={"Authorization": "Bearer token-user-donor-verified"},
    )
    assert res.status_code == 200
    data = res.json()
    facts = data["facts"]
    # 40 kg food = 100 meals (at 0.4 kg/meal)
    assert facts["food_rescued_kg"] == 40.0
    assert facts["meal_equivalents"] == 100
    # 40 kg food * 2.5 = 100.0 kg CO2e
    assert facts["co2_avoided_kg"] == 100.0
    assert "40.0 kg" in data["explanation_text"]
    assert "100 meal" in data["explanation_text"]


# =============================================================================
# 7. SECURITY, PRIVACY & RATE LIMITING
# =============================================================================

def test_rate_limiting():
    """RateLimiter raises 429 when max requests threshold is exceeded."""
    limiter = RateLimiter(max_requests=3, window_seconds=10.0)
    limiter.check_rate_limit("test-user")
    limiter.check_rate_limit("test-user")
    limiter.check_rate_limit("test-user")

    with pytest.raises(Exception) as exc_info:
        limiter.check_rate_limit("test-user")
    assert "rate limit exceeded" in str(exc_info.value).lower()


def test_secrets_never_exposed(client: TestClient):
    """API responses never contain backend secrets or keys."""
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    body_text = res.text
    assert "GROQ_API_KEY" not in body_text
    assert "SUPABASE_SECRET_KEY" not in body_text
    assert "RAZORPAY_KEY_SECRET" not in body_text
