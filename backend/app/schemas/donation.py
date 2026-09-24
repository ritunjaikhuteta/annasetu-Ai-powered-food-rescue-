"""Pydantic schemas for Surplus Food Donations."""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, model_validator
from app.schemas.need import DietType


class StorageCondition(str, Enum):
    AMBIENT = "ambient"
    REFRIGERATED = "refrigerated"
    FROZEN = "frozen"
    HOT_HELD = "hot-held"


class DonationStatus(str, Enum):
    DRAFT = "DRAFT"
    POSTED = "POSTED"
    MATCHING = "MATCHING"
    MATCHED = "MATCHED"
    ALLOCATED = "ALLOCATED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"


class DonationBase(BaseModel):
    diet_type: DietType
    food_category_id: str = Field(..., description="Food Category UUID")
    declared_quantity_kg: float = Field(..., ge=5.0, description="Declared quantity in kg (minimum 5 kg)")
    preparation_at: str = Field(..., description="ISO 8601 preparation timestamp")
    available_from: str = Field(..., description="ISO 8601 pickup availability start")
    rescue_deadline: str = Field(..., description="ISO 8601 safe consumption/rescue deadline")
    storage_condition: StorageCondition = StorageCondition.AMBIENT
    packaging_type: str = Field(..., min_length=2, max_length=150)
    allergen_information: Optional[str] = None
    raw_description: str = Field(..., min_length=3, max_length=1000)
    normalized_description: Optional[str] = None
    image_path: Optional[str] = None
    pickup_location_id: str = Field(..., description="Donor pickup location UUID")

    @model_validator(mode="after")
    def validate_deadline_after_availability(self) -> "DonationBase":
        if self.rescue_deadline <= self.available_from:
            raise ValueError("rescue_deadline must be strictly after available_from.")
        return self


class DonationCreate(DonationBase):
    pass


class DonationUpdate(BaseModel):
    diet_type: Optional[DietType] = None
    food_category_id: Optional[str] = None
    declared_quantity_kg: Optional[float] = Field(None, ge=5.0)
    preparation_at: Optional[str] = None
    available_from: Optional[str] = None
    rescue_deadline: Optional[str] = None
    storage_condition: Optional[StorageCondition] = None
    packaging_type: Optional[str] = None
    allergen_information: Optional[str] = None
    raw_description: Optional[str] = None
    normalized_description: Optional[str] = None
    image_path: Optional[str] = None
    pickup_location_id: Optional[str] = None


class DonationResponse(BaseModel):
    id: str
    donor_id: str
    diet_type: DietType
    food_category_id: str
    declared_quantity_kg: float
    remaining_quantity_kg: float
    preparation_at: str
    available_from: str
    rescue_deadline: str
    storage_condition: StorageCondition
    packaging_type: str
    allergen_information: Optional[str] = None
    raw_description: str
    normalized_description: Optional[str] = None
    image_path: Optional[str] = None
    pickup_location_id: str
    status: DonationStatus
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
