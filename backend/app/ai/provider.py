"""Abstract Base Class for AI Providers in AnnaSetu."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class AIProvider(ABC):
    """Abstract interface decoupling business logic from any specific AI SDK or vendor."""

    @abstractmethod
    async def extract_document_data(
        self,
        doc_type: Optional[str],
        ocr_text: str,
    ) -> Dict[str, Any]:
        """Interprets raw OCR text or document content to extract candidate fields.
        
        Returns:
            Dict containing document_type, fields dict, confidence, and uncertainties.
        """
        pass

    @abstractmethod
    async def normalize_food_description(
        self,
        raw_description: str,
    ) -> Dict[str, Any]:
        """Extracts structured candidate food attributes from free-text description.
        
        Returns:
            Dict containing normalized_description, possible_category, possible_diet_type,
            estimated_quantity_kg, meal_period, possible_allergens, uncertainties.
        """
        pass

    @abstractmethod
    async def generate_explanation(
        self,
        explanation_type: str,
        context: Dict[str, Any],
    ) -> str:
        """Generates natural language operational explanations based strictly on deterministic facts.
        
        Args:
            explanation_type: MATCH_PRIORITY | DELIVERY_STATUS | IMPACT_SUMMARY
            context: Dictionary of authoritative factual numbers/states.
            
        Returns:
            Natural language explanation string.
        """
        pass

    @abstractmethod
    async def analyze_package_integrity(
        self,
        pickup_image: str,
        delivery_image: str,
    ) -> Dict[str, Any]:
        """Analyzes package visual consistency between pickup and delivery checkpoints.
        
        Reuses Phase 14 visual integrity check abstraction.
        Returns:
            Dict containing integrity_score, tampering_signal, reason, available.
        """
        pass
