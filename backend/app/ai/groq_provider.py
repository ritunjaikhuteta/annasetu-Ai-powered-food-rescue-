"""Groq AI Provider Implementation with Isolation, Timeouts, and Strict Validation."""

import json
import logging
import time
from typing import Any, Dict, Optional
import httpx
from app.ai.prompts import (
    DELIVERY_STATUS_SYSTEM_PROMPT,
    DOCUMENT_EXTRACTION_SYSTEM_PROMPT,
    FOOD_NORMALIZATION_SYSTEM_PROMPT,
    IMPACT_EXPLANATION_SYSTEM_PROMPT,
    MATCH_EXPLANATION_SYSTEM_PROMPT,
)
from app.ai.provider import AIProvider
from app.core.config import settings
from app.services.integrity_service import GroqVisionIntegrityAnalyzer

logger = logging.getLogger("annasetu.ai.groq")


class GroqProvider(AIProvider):
    """Groq-backed AI provider with non-blocking graceful fallbacks and strict validation."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
        vision_model: Optional[str] = None,
        enabled: Optional[bool] = None,
        timeout: Optional[float] = None,
    ):
        self.api_key = api_key or settings.GROQ_API_KEY
        self.model = model or settings.GROQ_MODEL
        self.vision_model = vision_model or settings.GROQ_VISION_MODEL
        self.enabled = settings.AI_ENABLED if enabled is None else enabled
        self.timeout = timeout or settings.AI_REQUEST_TIMEOUT_SECONDS
        self.endpoint = "https://api.groq.com/openai/v1/chat/completions"
        self._vision_analyzer = GroqVisionIntegrityAnalyzer(api_key=self.api_key)

    @property
    def is_available(self) -> bool:
        return bool(self.enabled and self.api_key and self.api_key.strip())

    async def _call_chat_completion(
        self,
        system_prompt: str,
        user_prompt: str,
        max_retries: int = 1,
    ) -> Optional[Dict[str, Any]]:
        """Invokes Groq Chat Completion with strict JSON output, retry, and timeout."""
        if not self.is_available:
            logger.info("AI provider is disabled or missing GROQ_API_KEY. Gracefully bypassing.")
            return None

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.1,
            "response_format": {"type": "json_object"},
        }

        attempts = 0
        start_time = time.perf_counter()

        while attempts <= max_retries:
            attempts += 1
            try:
                async with httpx.AsyncClient(timeout=self.timeout) as client:
                    res = await client.post(self.endpoint, headers=headers, json=payload)
                    duration_ms = (time.perf_counter() - start_time) * 1000

                    if res.status_code == 200:
                        data = res.json()
                        raw_content = data["choices"][0]["message"]["content"]
                        parsed = json.loads(raw_content)
                        logger.info("Groq chat completion succeeded (%.2fms, attempt %d)", duration_ms, attempts)
                        return parsed
                    else:
                        logger.warning(
                            "Groq API returned HTTP %d (attempt %d): %s",
                            res.status_code,
                            attempts,
                            res.text[:200],
                        )
            except (httpx.TimeoutException, httpx.RequestError) as net_err:
                logger.warning("Groq network error on attempt %d: %s", attempts, net_err)
            except json.JSONDecodeError as json_err:
                logger.warning("Groq response was not valid JSON on attempt %d: %s", attempts, json_err)
            except Exception as exc:
                logger.error("Unexpected error during Groq API call on attempt %d: %s", attempts, exc)

        logger.error("Groq chat completion failed after %d attempts. Returning None.", attempts)
        return None

    async def extract_document_data(
        self,
        doc_type: Optional[str],
        ocr_text: str,
    ) -> Dict[str, Any]:
        """Candidate extraction of document fields from raw OCR text."""
        if not self.is_available or not ocr_text.strip():
            return {
                "document_type": doc_type or "OTHER",
                "fields": {},
                "confidence": 0,
                "uncertainties": ["AI assistance unavailable."],
            }

        user_content = f"Document Type Hint: {doc_type or 'Unknown'}\n\nVisible OCR Text Snippet:\n{ocr_text.strip()[:2000]}"
        result = await self._call_chat_completion(
            system_prompt=DOCUMENT_EXTRACTION_SYSTEM_PROMPT,
            user_prompt=user_content,
        )

        if not result or not isinstance(result, dict):
            return {
                "document_type": doc_type or "OTHER",
                "fields": {},
                "confidence": 0,
                "uncertainties": ["AI document extraction failed or timed out."],
            }

        return {
            "document_type": result.get("document_type", doc_type or "OTHER"),
            "fields": result.get("fields", {}),
            "confidence": min(max(int(result.get("confidence", 50)), 0), 100),
            "uncertainties": result.get("uncertainties", []),
        }

    async def normalize_food_description(
        self,
        raw_description: str,
    ) -> Dict[str, Any]:
        """Normalizes food description into structured candidate category, diet, and quantity."""
        if not self.is_available:
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
        result = await self._call_chat_completion(
            system_prompt=FOOD_NORMALIZATION_SYSTEM_PROMPT,
            user_prompt=user_content,
        )

        if not result or not isinstance(result, dict):
            return {
                "normalized_description": raw_description.strip(),
                "possible_category": None,
                "possible_diet_type": None,
                "estimated_quantity_kg": None,
                "meal_period": None,
                "possible_allergens": [],
                "uncertainties": ["AI normalization unavailable."],
            }

        return {
            "normalized_description": str(result.get("normalized_description") or raw_description.strip()),
            "possible_category": result.get("possible_category"),
            "possible_diet_type": result.get("possible_diet_type"),
            "estimated_quantity_kg": float(result["estimated_quantity_kg"]) if result.get("estimated_quantity_kg") is not None else None,
            "meal_period": result.get("meal_period"),
            "possible_allergens": result.get("possible_allergens", []),
            "uncertainties": result.get("uncertainties", []),
        }

    async def generate_explanation(
        self,
        explanation_type: str,
        context: Dict[str, Any],
    ) -> str:
        """Generates natural language explanation grounded strictly in deterministic facts."""
        if not self.is_available:
            return self._deterministic_explanation_fallback(explanation_type, context)

        # Select matching system prompt
        if explanation_type == "MATCH_PRIORITY":
            prompt = MATCH_EXPLANATION_SYSTEM_PROMPT
        elif explanation_type == "DELIVERY_STATUS":
            prompt = DELIVERY_STATUS_SYSTEM_PROMPT
        elif explanation_type == "IMPACT_SUMMARY":
            prompt = IMPACT_EXPLANATION_SYSTEM_PROMPT
        else:
            return self._deterministic_explanation_fallback(explanation_type, context)

        user_content = f"Deterministic operational facts:\n{json.dumps(context, default=str)}"
        result = await self._call_chat_completion(system_prompt=prompt, user_prompt=user_content)

        if result and isinstance(result, dict) and "explanation_text" in result:
            return str(result["explanation_text"])

        return self._deterministic_explanation_fallback(explanation_type, context)

    def _deterministic_explanation_fallback(
        self,
        explanation_type: str,
        context: Dict[str, Any],
    ) -> str:
        """Deterministic, guaranteed template explanations when AI is offline or disabled."""
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
        """Reuses Phase 14 GroqVisionIntegrityAnalyzer."""
        return await self._vision_analyzer.analyze_package_integrity(
            pickup_image=pickup_image,
            delivery_image=delivery_image,
        )
