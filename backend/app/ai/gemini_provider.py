"""Google Gemini AI Provider Implementation with Isolation, Timeouts, and Strict Validation."""

import asyncio
import json
import logging
import time
from typing import Any, Dict, Optional

from google import genai
from google.genai import types

from app.ai.prompts import (
    DELIVERY_STATUS_SYSTEM_PROMPT,
    DOCUMENT_EXTRACTION_SYSTEM_PROMPT,
    FOOD_NORMALIZATION_SYSTEM_PROMPT,
    FOOD_QUALITY_ASSESSMENT_PROMPT,
    IMPACT_EXPLANATION_SYSTEM_PROMPT,
    MATCH_EXPLANATION_SYSTEM_PROMPT,
)
from app.ai.provider import AIProvider
from app.core.config import settings

logger = logging.getLogger("annasetu.ai.gemini")


class GeminiProvider(AIProvider):
    """Google Gemini AI provider using official google-genai SDK."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        fallback_model: str = "gemini-1.5-flash",
        enabled: Optional[bool] = None,
        timeout: Optional[float] = None,
        fallback_provider: Optional[AIProvider] = None,
    ):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model = model or settings.GEMINI_MODEL
        self.fallback_model = fallback_model
        self.enabled = settings.AI_ENABLED if enabled is None else enabled
        self.timeout = timeout or settings.AI_REQUEST_TIMEOUT_SECONDS
        self.fallback_provider = fallback_provider
        self._client: Optional[genai.Client] = None

        if self.api_key and self.api_key.strip():
            try:
                self._client = genai.Client(api_key=self.api_key.strip())
            except Exception as e:
                logger.warning("Failed to initialize Google GenAI Client: %s", e)

    @property
    def is_available(self) -> bool:
        return bool(self.enabled and self.api_key and self.api_key.strip() and self._client is not None)

    async def _generate_content_with_retry(
        self,
        contents: Any,
        system_instruction: Optional[str] = None,
        response_mime_type: Optional[str] = "application/json",
        max_retries: int = 1,
    ) -> Optional[str]:
        """Calls Gemini aio.models.generate_content with timeout, retry, and fallback model."""
        if not self.is_available:
            return None

        models_to_try = [self.model]
        if self.fallback_model and self.fallback_model != self.model:
            models_to_try.append(self.fallback_model)

        for current_model in models_to_try:
            attempts = 0
            while attempts <= max_retries:
                attempts += 1
                try:
                    config = types.GenerateContentConfig(
                        temperature=0.1,
                        response_mime_type=response_mime_type,
                        system_instruction=system_instruction,
                    )
                    start_time = time.perf_counter()
                    
                    response = await asyncio.wait_for(
                        self._client.aio.models.generate_content(
                            model=current_model,
                            contents=contents,
                            config=config,
                        ),
                        timeout=self.timeout,
                    )
                    duration_ms = (time.perf_counter() - start_time) * 1000
                    logger.info("Gemini generate_content succeeded on %s (%.2fms)", current_model, duration_ms)
                    return response.text
                except asyncio.TimeoutError:
                    logger.warning("Gemini call timed out on %s (attempt %d)", current_model, attempts)
                except Exception as exc:
                    logger.warning("Gemini error on %s (attempt %d): %s", current_model, attempts, exc)
                    break  # If model not found or fatal error, try fallback model instead of retrying immediately

        return None

    async def analyze_food_quality(
        self,
        image_bytes: bytes,
        mime_type: str = "image/jpeg",
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Visual inspection of surplus food image using Gemini multimodal vision."""
        if not image_bytes:
            return {
                "food_identified": None,
                "visual_quality_score": 0,
                "freshness_signal": "UNKNOWN",
                "packaging_condition": "NOT_VISIBLE",
                "image_quality": "INSUFFICIENT",
                "visible_concerns": ["No image bytes provided."],
                "risk_flags": ["MISSING_IMAGE"],
                "confidence": 0,
                "recommendation": "INSUFFICIENT_IMAGE",
                "explanation": "No food image provided for visual assessment.",
                "disclaimer": "Visual AI observation only. Not a food safety certification or shelf-life guarantee.",
                "provider": "gemini",
            }

        if not self.is_available:
            if self.fallback_provider:
                logger.info("Gemini unavailable. Delegating analyze_food_quality to fallback provider.")
                return await self.fallback_provider.analyze_food_quality(image_bytes, mime_type, context)
            return self._heuristic_food_quality_fallback(context)

        try:
            image_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
            prompt_text = "Examine this surplus food donation image and return structured visual quality assessment JSON."
            if context:
                prompt_text += f"\nContext details:\n{json.dumps(context, default=str)}"

            raw_text = await self._generate_content_with_retry(
                contents=[image_part, prompt_text],
                system_instruction=FOOD_QUALITY_ASSESSMENT_PROMPT,
                response_mime_type="application/json",
            )

            if raw_text:
                parsed = json.loads(raw_text.strip())
                score = int(parsed.get("visual_quality_score", 70))
                score = max(0, min(100, score))
                confidence = int(parsed.get("confidence", 50))
                confidence = max(0, min(100, confidence))

                return {
                    "food_identified": parsed.get("food_identified"),
                    "visual_quality_score": score,
                    "freshness_signal": str(parsed.get("freshness_signal", "UNKNOWN")).upper(),
                    "packaging_condition": str(parsed.get("packaging_condition", "NOT_VISIBLE")).upper(),
                    "image_quality": str(parsed.get("image_quality", "FAIR")).upper(),
                    "visible_concerns": parsed.get("visible_concerns", []),
                    "risk_flags": parsed.get("risk_flags", []),
                    "confidence": confidence,
                    "recommendation": str(parsed.get("recommendation", "MANUAL_REVIEW")).upper(),
                    "explanation": str(parsed.get("explanation", "Visual assessment completed.")),
                    "disclaimer": "Visual AI observation only. Not a food safety certification or shelf-life guarantee.",
                    "provider": "gemini",
                }
        except Exception as exc:
            logger.warning("Gemini food quality assessment failed: %s", exc)

        if self.fallback_provider:
            logger.info("Gemini call failed. Attempting fallback provider for food quality.")
            return await self.fallback_provider.analyze_food_quality(image_bytes, mime_type, context)

        return self._heuristic_food_quality_fallback(context)

    def _heuristic_food_quality_fallback(self, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        return {
            "food_identified": context.get("title") if context else "Food items",
            "visual_quality_score": 75,
            "freshness_signal": "UNKNOWN",
            "packaging_condition": "NOT_VISIBLE",
            "image_quality": "FAIR",
            "visible_concerns": ["AI visual analysis offline or non-responsive."],
            "risk_flags": [],
            "confidence": 50,
            "recommendation": "MANUAL_REVIEW",
            "explanation": "Visual assessment fallback: AI inspection offline. Manual verification recommended.",
            "disclaimer": "Visual AI observation only. Not a food safety certification or shelf-life guarantee.",
            "provider": "gemini",
        }

    async def extract_document_data(
        self,
        doc_type: Optional[str],
        ocr_text: str,
    ) -> Dict[str, Any]:
        """Candidate extraction of document fields from raw OCR text using Gemini."""
        if not self.is_available or not ocr_text.strip():
            if self.fallback_provider:
                return await self.fallback_provider.extract_document_data(doc_type, ocr_text)
            return {
                "document_type": doc_type or "OTHER",
                "fields": {},
                "confidence": 0,
                "uncertainties": ["AI assistance unavailable."],
            }

        user_content = f"Document Type Hint: {doc_type or 'Unknown'}\n\nVisible OCR Text Snippet:\n{ocr_text.strip()[:2000]}"
        raw_text = await self._generate_content_with_retry(
            contents=user_content,
            system_instruction=DOCUMENT_EXTRACTION_SYSTEM_PROMPT,
        )

        if raw_text:
            try:
                result = json.loads(raw_text.strip())
                return {
                    "document_type": result.get("document_type", doc_type or "OTHER"),
                    "fields": result.get("fields", {}),
                    "confidence": min(max(int(result.get("confidence", 50)), 0), 100),
                    "uncertainties": result.get("uncertainties", []),
                }
            except Exception:
                pass

        if self.fallback_provider:
            return await self.fallback_provider.extract_document_data(doc_type, ocr_text)

        return {
            "document_type": doc_type or "OTHER",
            "fields": {},
            "confidence": 0,
            "uncertainties": ["AI document extraction failed or timed out."],
        }

    async def normalize_food_description(
        self,
        raw_description: str,
    ) -> Dict[str, Any]:
        """Normalizes food description into structured candidate category, diet, and quantity."""
        if not self.is_available or not raw_description.strip():
            if self.fallback_provider:
                return await self.fallback_provider.normalize_food_description(raw_description)
            return {
                "normalized_description": raw_description.strip(),
                "possible_category": None,
                "possible_diet_type": None,
                "estimated_quantity_kg": None,
                "meal_period": None,
                "possible_allergens": [],
                "uncertainties": ["AI assistance unavailable."],
            }

        user_content = f"Raw food description to interpret:\n{raw_description.strip()[:500]}"
        raw_text = await self._generate_content_with_retry(
            contents=user_content,
            system_instruction=FOOD_NORMALIZATION_SYSTEM_PROMPT,
        )

        if raw_text:
            try:
                result = json.loads(raw_text.strip())
                return {
                    "normalized_description": str(result.get("normalized_description") or raw_description.strip()),
                    "possible_category": result.get("possible_category"),
                    "possible_diet_type": result.get("possible_diet_type"),
                    "estimated_quantity_kg": float(result["estimated_quantity_kg"]) if result.get("estimated_quantity_kg") is not None else None,
                    "meal_period": result.get("meal_period"),
                    "possible_allergens": result.get("possible_allergens", []),
                    "uncertainties": result.get("uncertainties", []),
                }
            except Exception:
                pass

        if self.fallback_provider:
            return await self.fallback_provider.normalize_food_description(raw_description)

        return {
            "normalized_description": raw_description.strip(),
            "possible_category": None,
            "possible_diet_type": None,
            "estimated_quantity_kg": None,
            "meal_period": None,
            "possible_allergens": [],
            "uncertainties": ["AI normalization unavailable."],
        }

    async def generate_explanation(
        self,
        explanation_type: str,
        context: Dict[str, Any],
    ) -> str:
        """Generates natural language explanation grounded strictly in deterministic facts."""
        if not self.is_available:
            if self.fallback_provider:
                return await self.fallback_provider.generate_explanation(explanation_type, context)
            return self._deterministic_explanation_fallback(explanation_type, context)

        if explanation_type == "MATCH_PRIORITY":
            prompt = MATCH_EXPLANATION_SYSTEM_PROMPT
        elif explanation_type == "DELIVERY_STATUS":
            prompt = DELIVERY_STATUS_SYSTEM_PROMPT
        elif explanation_type == "IMPACT_SUMMARY":
            prompt = IMPACT_EXPLANATION_SYSTEM_PROMPT
        else:
            return self._deterministic_explanation_fallback(explanation_type, context)

        user_content = f"Deterministic operational facts:\n{json.dumps(context, default=str)}"
        raw_text = await self._generate_content_with_retry(
            contents=user_content,
            system_instruction=prompt,
        )

        if raw_text:
            try:
                result = json.loads(raw_text.strip())
                if "explanation_text" in result:
                    return str(result["explanation_text"])
            except Exception:
                pass

        if self.fallback_provider:
            return await self.fallback_provider.generate_explanation(explanation_type, context)

        return self._deterministic_explanation_fallback(explanation_type, context)

    def _deterministic_explanation_fallback(
        self,
        explanation_type: str,
        context: Dict[str, Any],
    ) -> str:
        """Deterministic template explanation fallback."""
        if explanation_type == "MATCH_PRIORITY":
            score = context.get("priority_score", 0)
            dist = context.get("distance_km", 0.0)
            eta = context.get("estimated_travel_minutes", 0)
            buffer_hrs = context.get("shelf_life_buffer_hours", 0.0)
            label = context.get("priority_label", "MEDIUM")
            return (
                f"Rescue match ranked {label} (score {score}/100) based on {dist} km transit distance (~{eta} mins), "
                f"with a {buffer_hrs}h shelf-life safety buffer before expiry."
            )
        elif explanation_type == "DELIVERY_STATUS":
            state = context.get("status", "ACTIVE")
            stops = context.get("completed_stops", 0)
            total = context.get("total_stops", 1)
            return f"Delivery is {state}. Completed {stops} of {total} drop-off stops."
        elif explanation_type == "IMPACT_SUMMARY":
            kg = context.get("food_rescued_kg", 0.0)
            meals = context.get("meal_equivalents", 0)
            co2 = context.get("co2_avoided_kg", 0.0)
            return (
                f"Rescued {kg:.1f} kg of food, providing approximately {meals} meal equivalents "
                f"and avoiding {co2:.1f} kg of CO2e emissions."
            )
        return "Operational status updated."

    async def analyze_package_integrity(
        self,
        pickup_image: str,
        delivery_image: str,
    ) -> Dict[str, Any]:
        """Analyzes package integrity between pickup and delivery images."""
        if self.fallback_provider:
            return await self.fallback_provider.analyze_package_integrity(pickup_image, delivery_image)
        return {
            "integrity_score": None,
            "tampering_signal": False,
            "reason": "AI visual consistency check unavailable. Platform manual review available.",
            "available": False,
        }
