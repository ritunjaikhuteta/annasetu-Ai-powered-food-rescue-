"""AnnaSetu AI Assistance, OCR & Document Intelligence Service.

Authoritative constraints:
- Deterministic backend logic is authoritative for all operational decisions.
- AI is solely an assistance, OCR parsing, and explanation layer.
- AI must never independently approve/reject verification, matching, allocation, or payments.
- Core operations must continue when AI is unavailable.
"""

from collections import defaultdict
from datetime import date, datetime, timezone
import json
import logging
import re
import time
from typing import Any, Dict, List, Optional, Tuple
import uuid
import httpx
from app.ai.groq_provider import GroqProvider
from app.ai.provider import AIProvider
from app.ai.schemas import (
    ConsistencyCheckDetail,
    ConsistencyCheckStatus,
    DocumentConsistencyResponse,
    DocumentExtractionResult,
    DocumentReviewResult,
    DonationAIAssistResponse,
    ExplanationResponse,
    ExtractedDocumentFields,
    FoodNormalizationResponse,
    FoodQualityAssessment,
    NeedAIAssistResponse,
)
from app.core.config import settings
from app.db.supabase import SupabaseClient
from app.services.audit_service import AuditService
from app.utils.exceptions import AppException, ForbiddenException, NotFoundException, ValidationException

logger = logging.getLogger("annasetu.ai.service")

# Regex patterns for deterministic parsing
QUANTITY_KG_REGEX = re.compile(
    r"(?P<qty>\d+(?:\.\d+)?)\s*(?P<unit>kgs?|kilograms?|kilo|kg)\b",
    re.IGNORECASE,
)
QUANTITY_GRAMS_REGEX = re.compile(
    r"(?P<qty>\d+(?:\.\d+)?)\s*(?P<unit>grams?|gm|g)\b",
    re.IGNORECASE,
)
DATE_REGEX = re.compile(
    r"\b(?P<year>20\d{2})[-/.](?P<month>0[1-9]|1[0-2])[-/.](?P<day>0[1-9]|[12]\d|3[01])\b|"
    r"\b(?P<day2>0[1-9]|[12]\d|3[01])[-/.](?P<month2>0[1-9]|1[0-2])[-/.](?P<year2>20\d{2})\b"
)
GSTIN_REGEX = re.compile(r"\b[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}\b")
PAN_REGEX = re.compile(r"\b[A-Z]{5}[0-9]{4}[A-Z]{1}\b")
FSSAI_REGEX = re.compile(r"\b[0-9]{14}\b")
VEHICLE_NUM_REGEX = re.compile(r"\b[A-Z]{2}[-\s]?[0-9]{1,2}[-\s]?[A-Z]{1,3}[-\s]?[0-9]{4}\b")

# Meal and Diet keywords for deterministic parsing
MEAL_PERIOD_KEYWORDS = {
    "BREAKFAST": ["breakfast", "morning", "nashta", "tiffin"],
    "LUNCH": ["lunch", "afternoon", "dopahar"],
    "DINNER": ["dinner", "night", "raat", "supper"],
    "SNACKS": ["snack", "snacks", "tea time", "evening snacks"],
}

DIET_KEYWORDS = {
    "VEGETARIAN": ["veg", "vegetarian", "shakahari", "pure veg"],
    "NON_VEGETARIAN": ["non-veg", "chicken", "meat", "mutton", "fish", "egg", "eggs"],
    "VEGAN": ["vegan", "plant-based"],
}


class RateLimiter:
    """In-memory sliding window rate limiter for expensive AI endpoints."""

    def __init__(self, max_requests: int = 20, window_seconds: float = 60.0):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._history: Dict[str, List[float]] = defaultdict(list)

    def check_rate_limit(self, key: str) -> None:
        now = time.time()
        cutoff = now - self.window_seconds
        # Evict old timestamps
        timestamps = [ts for ts in self._history[key] if ts > cutoff]
        if len(timestamps) >= self.max_requests:
            logger.warning("AI endpoint rate limit exceeded for key %s", key)
            raise AppException("AI request rate limit exceeded. Please wait a minute.", status_code=429)
        timestamps.append(now)
        self._history[key] = timestamps


ai_rate_limiter = RateLimiter(max_requests=25, window_seconds=60.0)


class AIService:
    """Core domain service for AnnaSetu AI assistance, OCR intelligence, and deterministic safeguards."""

    def __init__(
        self,
        db: SupabaseClient,
        provider: Optional[AIProvider] = None,
    ):
        self.db = db
        self.provider = provider or GroqProvider()
        self.audit = AuditService(db)

    # =========================================================================
    # 1. DETERMINISTIC OCR & DOCUMENT EXTRACTION
    # =========================================================================

    def _parse_dates_deterministically(self, text: str) -> List[str]:
        """Finds valid dates in text."""
        dates = []
        for m in DATE_REGEX.finditer(text):
            if m.group("year") and m.group("month") and m.group("day"):
                dates.append(f"{m.group('year')}-{m.group('month')}-{m.group('day')}")
            elif m.group("year2") and m.group("month2") and m.group("day2"):
                dates.append(f"{m.group('year2')}-{m.group('month2')}-{m.group('day2')}")
        return dates

    def _extract_document_fields_deterministic(
        self,
        doc_type: Optional[str],
        ocr_text: str,
    ) -> ExtractedDocumentFields:
        """Deterministic regex parsing for standard document types."""
        clean_text = ocr_text.upper()
        fields = ExtractedDocumentFields(document_type=doc_type)

        # Vehicle number
        veh_match = VEHICLE_NUM_REGEX.search(clean_text)
        if veh_match:
            fields.vehicle_number = veh_match.group(0).replace(" ", "-")

        # GSTIN
        gstin_match = GSTIN_REGEX.search(clean_text)
        if gstin_match:
            fields.document_number = gstin_match.group(0)
            if not fields.document_type:
                fields.document_type = "GST_REGISTRATION"

        # PAN
        pan_match = PAN_REGEX.search(clean_text)
        if pan_match and not fields.document_number:
            fields.document_number = pan_match.group(0)
            if not fields.document_type:
                fields.document_type = "PAN"

        # FSSAI
        fssai_match = FSSAI_REGEX.search(clean_text)
        if fssai_match and not fields.document_number:
            fields.document_number = fssai_match.group(0)
            if not fields.document_type:
                fields.document_type = "FSSAI_LICENSE"

        # Dates (issue / expiry)
        dates = self._parse_dates_deterministically(ocr_text)
        if len(dates) >= 2:
            sorted_dates = sorted(dates)
            fields.issue_date = sorted_dates[0]
            fields.expiry_date = sorted_dates[-1]
        elif len(dates) == 1:
            fields.issue_date = dates[0]

        return fields

    async def process_verification_document(
        self,
        document_id: str,
        user_id: str,
        raw_ocr_text: Optional[str] = None,
        doc_type_hint: Optional[str] = None,
    ) -> DocumentExtractionResult:
        """Processes an uploaded document, parses candidates, and updates verification_documents.extracted_data."""
        ai_rate_limiter.check_rate_limit(f"doc_{user_id}")

        # Fetch existing document
        doc = await self.db.get_by_id("verification_documents", document_id, id_column="id")
        if not doc:
            raise NotFoundException(f"Verification document {document_id} not found.")

        ocr_content = raw_ocr_text or doc.get("raw_text") or doc.get("file_name") or ""
        doc_type = doc_type_hint or doc.get("document_type") or "OTHER"

        # 1. Deterministic extraction first
        fields = self._extract_document_fields_deterministic(doc_type, ocr_content)
        method = "DETERMINISTIC"
        confidence = 70.0
        uncertainties: List[str] = []

        # 2. If critical fields are missing and AI is enabled, call AI provider for assistance
        if (not fields.document_number or not fields.holder_name) and self.provider:
            try:
                ai_res = await self.provider.extract_document_data(doc_type, ocr_content)
                ai_fields = ai_res.get("fields", {})
                if ai_fields and isinstance(ai_fields, dict):
                    method = "AI_ASSISTED"
                    confidence = float(ai_res.get("confidence", 60.0))
                    uncertainties = ai_res.get("uncertainties", [])

                    # Complement missing fields from AI without overwriting deterministic regex matches
                    if not fields.document_number and ai_fields.get("document_number"):
                        fields.document_number = str(ai_fields["document_number"]).strip()
                    if not fields.holder_name and ai_fields.get("holder_name"):
                        fields.holder_name = str(ai_fields["holder_name"]).strip()
                    if not fields.organization_name and ai_fields.get("organization_name"):
                        fields.organization_name = str(ai_fields["organization_name"]).strip()
                    if not fields.vehicle_number and ai_fields.get("vehicle_number"):
                        fields.vehicle_number = str(ai_fields["vehicle_number"]).strip()
                    if not fields.expiry_date and ai_fields.get("expiry_date"):
                        fields.expiry_date = str(ai_fields["expiry_date"]).strip()
                    if not fields.issue_date and ai_fields.get("issue_date"):
                        fields.issue_date = str(ai_fields["issue_date"]).strip()
            except Exception as exc:
                logger.warning("AI document extraction failed gracefully: %s", exc)
                uncertainties.append("AI assistance unavailable; deterministic extraction used.")

        # Determine review status (AI never creates VERIFIED status!)
        review_status = DocumentReviewResult.EXTRACTED_SUCCESSFULLY
        if not fields.document_number and not fields.holder_name and not fields.organization_name:
            review_status = DocumentReviewResult.EXTRACTION_UNCERTAIN
            uncertainties.append("Document number and holder could not be extracted with confidence.")

        # Store candidate extraction in verification_documents.extracted_data (Section 5)
        extracted_payload = {
            "document_type": doc_type,
            "document_number": fields.document_number,
            "holder_name": fields.holder_name,
            "organization_name": fields.organization_name,
            "vehicle_number": fields.vehicle_number,
            "issue_date": fields.issue_date,
            "expiry_date": fields.expiry_date,
            "issuing_authority": fields.issuing_authority,
            "extraction_confidence": confidence,
            "method": method,
            "extracted_at": datetime.now(timezone.utc).isoformat(),
        }

        # Keep original document metadata; never change status to VERIFIED here
        update_data = {
            "extracted_data": extracted_payload,
            "verification_status": "MANUAL_REVIEW",  # moves to MANUAL_REVIEW, never VERIFIED
            "updated_at": datetime.now(timezone.utc).isoformat(),
        }
        await self.db.update_by_id("verification_documents", document_id, update_data)

        # Audit log event
        await self.audit.log_event(
            action="DOCUMENT_CANDIDATE_DATA_EXTRACTED",
            entity_type="verification_documents",
            entity_id=document_id,
            user_id=user_id,
            new_values={"method": method, "confidence": confidence, "review_status": review_status.value},
        )

        return DocumentExtractionResult(
            document_id=document_id,
            document_type=doc_type,
            fields=fields,
            confidence=confidence,
            uncertainties=uncertainties,
            method=method,
            review_status=review_status,
            stored_in_db=True,
        )

    # =========================================================================
    # 2. DOCUMENT CONSISTENCY CHECKS
    # =========================================================================

    async def check_document_consistency(
        self,
        document_id: str,
        user_id: str,
    ) -> DocumentConsistencyResponse:
        """Performs deterministic consistency checks between document candidate fields and registered profiles."""
        doc = await self.db.get_by_id("verification_documents", document_id, id_column="id")
        if not doc:
            raise NotFoundException(f"Verification document {document_id} not found.")

        extracted = doc.get("extracted_data") or {}
        details: List[ConsistencyCheckDetail] = []
        is_expired = False
        mismatch_found = False

        # 1. Expiry check against current UTC date
        expiry_str = extracted.get("expiry_date")
        if expiry_str:
            try:
                exp_date = datetime.strptime(expiry_str[:10], "%Y-%m-%d").date()
                today = datetime.now(timezone.utc).date()
                if exp_date < today:
                    is_expired = True
                    details.append(ConsistencyCheckDetail(
                        field_name="expiry_date",
                        extracted_value=expiry_str,
                        profile_value=today.isoformat(),
                        status=ConsistencyCheckStatus.MISMATCH,
                        reason=f"Document expired on {expiry_str}.",
                    ))
                else:
                    details.append(ConsistencyCheckDetail(
                        field_name="expiry_date",
                        extracted_value=expiry_str,
                        profile_value=today.isoformat(),
                        status=ConsistencyCheckStatus.MATCH,
                        reason=f"Document is valid until {expiry_str}.",
                    ))
            except Exception:
                details.append(ConsistencyCheckDetail(
                    field_name="expiry_date",
                    extracted_value=expiry_str,
                    status=ConsistencyCheckStatus.NOT_CHECKED,
                    reason="Invalid date format in extracted expiry date.",
                ))

        # 2. Profiles comparison
        profile = await self.db.get_by_id("profiles", user_id, id_column="id") or {}
        donor_prof = await self.db.get_by_id("donor_profiles", user_id, id_column="user_id") or {}
        receiver_prof = await self.db.get_by_id("receiver_profiles", user_id, id_column="user_id") or {}
        driver_prof = await self.db.get_by_id("driver_profiles", user_id, id_column="user_id") or {}

        # Holder Name vs registered full name
        extracted_holder = extracted.get("holder_name")
        registered_name = profile.get("full_name")
        if extracted_holder and registered_name:
            if extracted_holder.strip().upper() == registered_name.strip().upper():
                details.append(ConsistencyCheckDetail(
                    field_name="holder_name",
                    extracted_value=extracted_holder,
                    profile_value=registered_name,
                    status=ConsistencyCheckStatus.MATCH,
                    reason="Document holder matches profile full name.",
                ))
            elif any(part in extracted_holder.upper() for part in registered_name.upper().split()):
                details.append(ConsistencyCheckDetail(
                    field_name="holder_name",
                    extracted_value=extracted_holder,
                    profile_value=registered_name,
                    status=ConsistencyCheckStatus.PARTIAL_MATCH,
                    reason="Document holder name partially matches profile full name.",
                ))
            else:
                mismatch_found = True
                details.append(ConsistencyCheckDetail(
                    field_name="holder_name",
                    extracted_value=extracted_holder,
                    profile_value=registered_name,
                    status=ConsistencyCheckStatus.MISMATCH,
                    reason="Holder name does not match registered representative name.",
                ))

        # Organization Name vs Receiver / Donor profile
        extracted_org = extracted.get("organization_name")
        reg_org = receiver_prof.get("organization_name") or donor_prof.get("business_name")
        if extracted_org and reg_org:
            if extracted_org.strip().upper() == reg_org.strip().upper():
                details.append(ConsistencyCheckDetail(
                    field_name="organization_name",
                    extracted_value=extracted_org,
                    profile_value=reg_org,
                    status=ConsistencyCheckStatus.MATCH,
                    reason="Organization name matches registered organization.",
                ))
            elif any(w in extracted_org.upper() for w in reg_org.upper().split() if len(w) > 3):
                details.append(ConsistencyCheckDetail(
                    field_name="organization_name",
                    extracted_value=extracted_org,
                    profile_value=reg_org,
                    status=ConsistencyCheckStatus.PARTIAL_MATCH,
                    reason="Organization name partially matches registered entity.",
                ))
            else:
                mismatch_found = True
                details.append(ConsistencyCheckDetail(
                    field_name="organization_name",
                    extracted_value=extracted_org,
                    profile_value=reg_org,
                    status=ConsistencyCheckStatus.MISMATCH,
                    reason="Organization name mismatch.",
                ))

        # Vehicle number vs Driver Profile
        extracted_veh = extracted.get("vehicle_number")
        reg_veh = driver_prof.get("vehicle_number")
        if extracted_veh and reg_veh:
            clean_ext_v = re.sub(r"[^A-Z0-9]", "", extracted_veh.upper())
            clean_reg_v = re.sub(r"[^A-Z0-9]", "", reg_veh.upper())
            if clean_ext_v == clean_reg_v:
                details.append(ConsistencyCheckDetail(
                    field_name="vehicle_number",
                    extracted_value=extracted_veh,
                    profile_value=reg_veh,
                    status=ConsistencyCheckStatus.MATCH,
                    reason="Vehicle registration plate matches driver profile.",
                ))
            else:
                mismatch_found = True
                details.append(ConsistencyCheckDetail(
                    field_name="vehicle_number",
                    extracted_value=extracted_veh,
                    profile_value=reg_veh,
                    status=ConsistencyCheckStatus.MISMATCH,
                    reason="Vehicle number does not match registered vehicle plate.",
                ))

        # Overall Status
        if is_expired:
            overall = ConsistencyCheckStatus.MISMATCH
            rec = DocumentReviewResult.EXPIRED_DOCUMENT
        elif mismatch_found:
            overall = ConsistencyCheckStatus.MISMATCH
            rec = DocumentReviewResult.DOCUMENT_MISMATCH
        elif any(d.status == ConsistencyCheckStatus.PARTIAL_MATCH for d in details):
            overall = ConsistencyCheckStatus.PARTIAL_MATCH
            rec = DocumentReviewResult.MANUAL_REVIEW_REQUIRED
        elif any(d.status == ConsistencyCheckStatus.MATCH for d in details):
            overall = ConsistencyCheckStatus.MATCH
            rec = DocumentReviewResult.MANUAL_REVIEW_REQUIRED  # Admin still must review!
        else:
            overall = ConsistencyCheckStatus.NOT_CHECKED
            rec = DocumentReviewResult.MANUAL_REVIEW_REQUIRED

        audit_note = (
            "Consistency check completed. Evidence collected for human review. "
            "Deterministic rule: AI and checks cannot independently set status to VERIFIED."
        )

        return DocumentConsistencyResponse(
            document_id=document_id,
            overall_status=overall,
            is_expired=is_expired,
            review_recommendation=rec,
            details=details,
            audit_note=audit_note,
        )

    # =========================================================================
    # 3. FOOD DESCRIPTION NORMALIZATION
    # =========================================================================

    def _parse_food_deterministically(self, text: str) -> Dict[str, Any]:
        """Deterministic unit and keyword parsing before invoking AI."""
        clean = text.strip()
        result: Dict[str, Any] = {
            "normalized_description": clean,
            "possible_category": None,
            "possible_diet_type": None,
            "estimated_quantity_kg": None,
            "meal_period": None,
            "possible_allergens": [],
            "uncertainties": [],
        }

        # 1. Detect kg units (e.g., "25 KGS" -> 25.0, "25kg rice" -> 25.0)
        kg_match = QUANTITY_KG_REGEX.search(clean)
        if kg_match:
            try:
                result["estimated_quantity_kg"] = float(kg_match.group("qty"))
            except ValueError:
                pass

        # 2. Detect grams (e.g., "5000 grams" -> 5.0 kg)
        if result["estimated_quantity_kg"] is None:
            g_match = QUANTITY_GRAMS_REGEX.search(clean)
            if g_match:
                try:
                    result["estimated_quantity_kg"] = round(float(g_match.group("qty")) / 1000.0, 2)
                except ValueError:
                    pass

        # 3. Detect Meal Period
        lower_text = clean.lower()
        for meal, keywords in MEAL_PERIOD_KEYWORDS.items():
            if any(kw in lower_text for kw in keywords):
                result["meal_period"] = meal
                break

        # 4. Detect Diet Type
        for diet, keywords in DIET_KEYWORDS.items():
            if any(kw in lower_text for kw in keywords):
                result["possible_diet_type"] = diet
                break

        # 5. Detect Common Food Categories
        if any(w in lower_text for w in ["curry", "rice", "dal", "roti", "biryani", "gravy", "cooked", "hot"]):
            result["possible_category"] = "Cooked Meals"
        elif any(w in lower_text for w in ["vegetable", "tomato", "potato", "onion", "fruit", "apples"]):
            result["possible_category"] = "Raw Produce"
        elif any(w in lower_text for w in ["bread", "bun", "cake", "pastry"]):
            result["possible_category"] = "Bakery"
        elif any(w in lower_text for w in ["milk", "paneer", "curd", "cheese"]):
            result["possible_category"] = "Dairy"

        return result

    async def normalize_food_description(
        self,
        raw_description: str,
        user_id: Optional[str] = None,
    ) -> FoodNormalizationResponse:
        """Normalizes raw food text using deterministic extraction first, followed by AI interpretation."""
        if user_id:
            ai_rate_limiter.check_rate_limit(f"food_{user_id}")

        clean = raw_description.strip()
        det = self._parse_food_deterministically(clean)
        is_ai_used = False

        # If key attributes are ambiguous or missing, invoke AI provider
        if (det["possible_category"] is None or det["possible_diet_type"] is None) and self.provider:
            try:
                ai_res = await self.provider.normalize_food_description(clean)
                is_ai_used = True
                if not det["possible_category"] and ai_res.get("possible_category"):
                    det["possible_category"] = ai_res["possible_category"]
                if not det["possible_diet_type"] and ai_res.get("possible_diet_type"):
                    det["possible_diet_type"] = ai_res["possible_diet_type"]
                if det["estimated_quantity_kg"] is None and ai_res.get("estimated_quantity_kg") is not None:
                    det["estimated_quantity_kg"] = ai_res["estimated_quantity_kg"]
                if not det["meal_period"] and ai_res.get("meal_period"):
                    det["meal_period"] = ai_res["meal_period"]
                if ai_res.get("possible_allergens"):
                    det["possible_allergens"] = ai_res["possible_allergens"]
                if ai_res.get("uncertainties"):
                    det["uncertainties"].extend(ai_res["uncertainties"])
            except Exception as exc:
                logger.warning("AI food normalization failed gracefully: %s", exc)
                det["uncertainties"].append("AI assistance unavailable; deterministic extraction used.")

        return FoodNormalizationResponse(
            raw_description=clean,
            normalized_description=det["normalized_description"],
            possible_category=det["possible_category"],
            possible_diet_type=det["possible_diet_type"],
            estimated_quantity_kg=det["estimated_quantity_kg"],
            meal_period=det["meal_period"],
            possible_allergens=det["possible_allergens"],
            uncertainties=det["uncertainties"],
            is_ai_generated=is_ai_used,
        )

    # =========================================================================
    # 4. DONATION ASSISTANCE
    # =========================================================================

    async def assist_donation(
        self,
        donation_id: str,
        user_id: str,
    ) -> DonationAIAssistResponse:
        """Assists donor with suggestions. Declared quantity remains strictly authoritative."""
        donation = await self.db.get_by_id("donations", donation_id, id_column="id")
        if not donation:
            raise NotFoundException(f"Donation {donation_id} not found.")

        declared_qty = float(donation.get("quantity_kg", 0.0))
        raw_desc = donation.get("description") or donation.get("food_name") or ""

        # Normalize food description
        norm_res = await self.normalize_food_description(raw_desc, user_id=user_id)

        # Quantity consistency signal (Section 9: donor-declared quantity is authoritative!)
        est_qty = norm_res.estimated_quantity_kg
        signal = "NOT_ESTIMATED"
        if est_qty is not None:
            diff_ratio = abs(est_qty - declared_qty) / max(declared_qty, 1.0)
            signal = "CONSISTENT" if diff_ratio <= 0.20 else "DISCREPANCY"

        # Missing information suggestions
        missing = []
        if not donation.get("storage_condition"):
            missing.append("Specify storage temperature (e.g. AMBIENT, CHILLED, HOT).")
        if not donation.get("packaging_type"):
            missing.append("Specify packaging type for transport safety (e.g. sealed containers, foil trays).")
        if not donation.get("shelf_life_hours"):
            missing.append("Add estimated shelf life in hours.")

        return DonationAIAssistResponse(
            donation_id=donation_id,
            declared_quantity_kg=declared_qty,
            normalized_description=norm_res.normalized_description,
            category_suggestion=norm_res.possible_category,
            diet_suggestion=norm_res.possible_diet_type,
            meal_period_suggestion=norm_res.meal_period,
            quantity_consistency_signal=signal,
            estimated_quantity_kg=est_qty,
            missing_information_suggestions=missing,
            allergen_suggestions=norm_res.possible_allergens,
        )

    # =========================================================================
    # 5. NEED ASSISTANCE
    # =========================================================================

    async def assist_need(
        self,
        need_id: str,
        user_id: str,
        free_text_requirement: Optional[str] = None,
    ) -> NeedAIAssistResponse:
        """Assists NGO receiver with structured suggestions from free text."""
        need = await self.db.get_by_id("ngo_needs", need_id, id_column="id")
        if not need:
            raise NotFoundException(f"Need {need_id} not found.")

        raw_text = free_text_requirement or need.get("notes") or need.get("special_instructions") or ""
        norm_res = await self.normalize_food_description(raw_text, user_id=user_id)

        special_reqs = []
        if norm_res.possible_allergens:
            special_reqs.append(f"Allergen restriction: Must be free of {', '.join(norm_res.possible_allergens)}.")
        if "hot" in raw_text.lower():
            special_reqs.append("Requires hot delivery container.")

        return NeedAIAssistResponse(
            need_id=need_id,
            suggested_meal_period=norm_res.meal_period,
            suggested_diet_type=norm_res.possible_diet_type,
            suggested_quantity_kg=norm_res.estimated_quantity_kg,
            special_requirements_suggestions=special_reqs,
            uncertainties=norm_res.uncertainties,
        )

    # =========================================================================
    # 6. HUMAN-READABLE EXPLANATIONS (MATCH, DELIVERY, IMPACT)
    # =========================================================================

    async def get_match_explanation(
        self,
        match_id: str,
        user_id: str,
    ) -> ExplanationResponse:
        """Explains deterministic match breakdown without modifying priority score."""
        match = await self.db.get_by_id("matches", match_id, id_column="id")
        if not match:
            raise NotFoundException(f"Match {match_id} not found.")

        facts = {
            "match_id": match_id,
            "priority_score": match.get("priority_score", 0),
            "priority_label": match.get("priority_label", "MEDIUM"),
            "distance_km": match.get("distance_km", 0.0),
            "estimated_travel_minutes": match.get("estimated_travel_minutes", 0),
            "shelf_life_buffer_hours": match.get("shelf_life_buffer_hours", 0.0),
            "fulfillment_ratio": match.get("fulfillment_ratio", 1.0),
        }

        explanation = await self.provider.generate_explanation(
            explanation_type="MATCH_PRIORITY",
            context=facts,
        )

        return ExplanationResponse(
            entity_id=match_id,
            explanation_type="MATCH_PRIORITY",
            explanation_text=explanation,
            is_ai_generated=getattr(self.provider, "is_available", False),
            facts=facts,
        )

    async def get_delivery_explanation(
        self,
        delivery_id: str,
        user_id: str,
    ) -> ExplanationResponse:
        """Explains delivery operational event from authoritative state."""
        delivery = await self.db.get_by_id("deliveries", delivery_id, id_column="id")
        if not delivery:
            raise NotFoundException(f"Delivery {delivery_id} not found.")

        stops = await self.db.query("delivery_stops", params={"delivery_id": f"eq.{delivery_id}"})
        completed_stops = len([s for s in stops if s.get("status") in ("COMPLETED", "DELIVERED")])

        facts = {
            "delivery_id": delivery_id,
            "status": delivery.get("status", "ACTIVE"),
            "completed_stops": completed_stops,
            "total_stops": len(stops) or 1,
            "current_stage": delivery.get("status"),
        }

        explanation = await self.provider.generate_explanation(
            explanation_type="DELIVERY_STATUS",
            context=facts,
        )

        return ExplanationResponse(
            entity_id=delivery_id,
            explanation_type="DELIVERY_STATUS",
            explanation_text=explanation,
            is_ai_generated=getattr(self.provider, "is_available", False),
            facts=facts,
        )

    async def get_impact_explanation(
        self,
        user_id: str,
        donation_id: Optional[str] = None,
    ) -> ExplanationResponse:
        """Explains impact numbers grounded strictly in recorded deterministic figures."""
        # Query impact_records or calculate strictly from deterministic formulas
        kg_rescued = 0.0
        if donation_id:
            donation = await self.db.get_by_id("donations", donation_id, id_column="id")
            if donation:
                kg_rescued = float(donation.get("quantity_kg", 0.0))
        else:
            records = await self.db.query("impact_records", params={"user_id": f"eq.{user_id}"})
            kg_rescued = sum(float(r.get("quantity_kg", 0.0)) for r in records)

        # Deterministic meal factor: 1 meal eq = 0.4 kg
        meals = int(kg_rescued / 0.4) if kg_rescued > 0 else 0
        co2_avoided = round(kg_rescued * 2.5, 2)  # Deterministic factor: 2.5 kg CO2e per kg food

        facts = {
            "user_id": user_id,
            "donation_id": donation_id,
            "food_rescued_kg": kg_rescued,
            "meal_equivalents": meals,
            "co2_avoided_kg": co2_avoided,
        }

        explanation = await self.provider.generate_explanation(
            explanation_type="IMPACT_SUMMARY",
            context=facts,
        )

        return ExplanationResponse(
            entity_id=donation_id or user_id,
            explanation_type="IMPACT_SUMMARY",
            explanation_text=explanation,
            is_ai_generated=getattr(self.provider, "is_available", False),
            facts=facts,
        )

    # =========================================================================
    # 7. VISUAL FOOD QUALITY ASSESSMENT (PHASE 21)
    # =========================================================================

    async def analyze_donation_food_quality(
        self,
        donation_id: str,
        user_id: str,
        user_role: str,
        raw_image_bytes: Optional[bytes] = None,
        mime_type: Optional[str] = None,
        image_url: Optional[str] = None,
        force_refresh: bool = False,
    ) -> FoodQualityAssessment:
        """Analyzes surplus food photo using visual AI observations.
        
        CRITICAL ARCHITECTURAL CONSTRAINTS:
        - Authoritative logic remains with deterministic rules & manual inspectors.
        - AI provides VISUAL QUALITY SCORE (0-100), visual signals, and manual review recommendations.
        - AI does NOT certify microbiological food safety, legal compliance, or expiry.
        - AI does NOT approve or reject donations.
        - Authorized callers: Donation donor owner or platform Admin.
        """
        # 1. Fetch donation record
        donation = await self.db.get_by_id("donations", donation_id, id_column="id")
        if not donation:
            raise NotFoundException(f"Donation {donation_id} not found.")

        # 2. Authorization check: Donor owner or Admin
        is_admin = user_role.upper() == "ADMIN"
        is_owner = str(donation.get("donor_id")) == str(user_id)
        if not (is_admin or is_owner):
            raise ForbiddenException("Only the donation owner or an administrator can request AI food quality assessment.")

        # 3. Rate limiting per user
        ai_rate_limiter.check_rate_limit(f"quality_{user_id}")

        # 4. Check for cached assessment if image source is unchanged and force_refresh is False
        target_image_ref = image_url or donation.get("image_path")
        if not force_refresh and not raw_image_bytes and donation.get("visual_quality_assessment"):
            cached_data = donation["visual_quality_assessment"]
            if isinstance(cached_data, dict) and cached_data.get("visual_quality_score") is not None:
                cached_src = cached_data.get("_image_source")
                if not cached_src or cached_src == target_image_ref:
                    cached_copy = dict(cached_data)
                    cached_copy["is_cached"] = True
                    cached_copy.pop("_image_source", None)
                    logger.info("Returning cached visual food quality assessment for donation %s", donation_id)
                    return FoodQualityAssessment(**cached_copy)

        # 5. Obtain image bytes
        img_bytes: Optional[bytes] = None
        detected_mime = mime_type or "image/jpeg"

        if raw_image_bytes:
            img_bytes = raw_image_bytes
        elif target_image_ref:
            if target_image_ref.startswith("data:image/"):
                import base64
                header, encoded = target_image_ref.split(",", 1)
                detected_mime = header.split(";")[0].replace("data:", "")
                img_bytes = base64.b64decode(encoded)
            elif target_image_ref.startswith("http://") or target_image_ref.startswith("https://"):
                try:
                    async with httpx.AsyncClient(timeout=10.0) as client:
                        resp = await client.get(target_image_ref)
                        if resp.status_code == 200:
                            img_bytes = resp.content
                            detected_mime = resp.headers.get("content-type") or detected_mime
                        else:
                            raise ValidationException(f"Failed to fetch food image from URL (HTTP {resp.status_code}).")
                except httpx.RequestError as exc:
                    raise ValidationException(f"Network error downloading food image: {str(exc)}")
            else:
                # Relative Supabase storage path
                supabase_url = settings.SUPABASE_URL.rstrip("/") if settings.SUPABASE_URL else ""
                if supabase_url:
                    full_url = f"{supabase_url}/storage/v1/object/public/donation-images/{target_image_ref.lstrip('/')}"
                    try:
                        async with httpx.AsyncClient(timeout=10.0) as client:
                            resp = await client.get(full_url)
                            if resp.status_code == 200:
                                img_bytes = resp.content
                                detected_mime = resp.headers.get("content-type") or detected_mime
                    except Exception as exc:
                        logger.warning("Could not download image from Supabase storage: %s", exc)

        if not img_bytes:
            raise ValidationException("No valid food image found for visual analysis. Please upload or specify an image.")

        # Size check (max 10MB)
        if len(img_bytes) > 10 * 1024 * 1024:
            raise ValidationException("Food image file exceeds maximum allowed size of 10MB.")

        # Clean mime
        clean_mime = detected_mime.split(";")[0].strip().lower()
        if clean_mime not in ("image/jpeg", "image/png", "image/webp", "image/jpg"):
            clean_mime = "image/jpeg"

        # 6. Prepare context details
        context = {
            "donation_id": donation_id,
            "raw_description": donation.get("raw_description"),
            "diet_type": donation.get("diet_type"),
            "storage_condition": donation.get("storage_condition"),
            "packaging_type": donation.get("packaging_type"),
            "declared_quantity_kg": donation.get("declared_quantity_kg"),
        }

        # 7. Audit log analysis request
        await self.audit.log_event(
            action="FOOD_QUALITY_ANALYSIS_REQUESTED",
            entity_type="donations",
            entity_id=donation_id,
            user_id=user_id,
            new_values={"image_source": target_image_ref or "direct_upload"},
        )

        # 8. Call AI Provider
        raw_result = await self.provider.analyze_food_quality(
            image_bytes=img_bytes,
            mime_type=clean_mime,
            context=context,
        )

        # 9. Format FoodQualityAssessment response
        now_iso = datetime.now(timezone.utc).isoformat()
        score = int(raw_result.get("visual_quality_score", 70))
        score = max(0, min(100, score))
        confidence = int(raw_result.get("confidence", 50))
        confidence = max(0, min(100, confidence))

        assessment = FoodQualityAssessment(
            donation_id=donation_id,
            food_identified=raw_result.get("food_identified"),
            visual_quality_score=score,
            freshness_signal=raw_result.get("freshness_signal", "UNKNOWN"),
            packaging_condition=raw_result.get("packaging_condition", "NOT_VISIBLE"),
            image_quality=raw_result.get("image_quality", "FAIR"),
            visible_concerns=raw_result.get("visible_concerns", []),
            risk_flags=raw_result.get("risk_flags", []),
            confidence=confidence,
            recommendation=raw_result.get("recommendation", "MANUAL_REVIEW"),
            explanation=raw_result.get("explanation", "Visual inspection completed."),
            disclaimer="Visual AI observation only. Not a food safety certification or shelf-life guarantee.",
            is_cached=False,
            provider=raw_result.get("provider", "gemini"),
            analyzed_at=now_iso,
        )

        # 10. Persist assessment on donation record (non-authoritative metadata)
        storage_dict = assessment.model_dump()
        storage_dict["_image_source"] = target_image_ref
        try:
            await self.db.update_by_id(
                "donations",
                donation_id,
                {
                    "visual_quality_assessment": storage_dict,
                    "updated_at": now_iso,
                },
            )
        except Exception as exc:
            logger.warning("Could not update donation with visual_quality_assessment: %s", exc)

        # 11. Audit log completion
        await self.audit.log_event(
            action="FOOD_QUALITY_ANALYSIS_COMPLETED",
            entity_type="donations",
            entity_id=donation_id,
            user_id=user_id,
            new_values={
                "visual_quality_score": score,
                "freshness_signal": assessment.freshness_signal.value,
                "recommendation": assessment.recommendation.value,
                "provider": assessment.provider,
            },
        )

        return assessment
