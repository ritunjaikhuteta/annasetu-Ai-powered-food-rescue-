"""Pydantic schemas for NGO Needs."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field, model_validator
from app.utils.exceptions import ValidationException


class MealPeriod(str, Enum):
    BREAKFAST = "BREAKFAST"
    LUNCH = "LUNCH"
    DINNER = "DINNER"
    SNACKS = "SNACKS"


class DietType(str, Enum):
    VEGETARIAN = "VEGETARIAN"
    NON_VEGETARIAN = "NON_VEGETARIAN"
    MIXED = "MIXED"


class NeedStatus(str, Enum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    PARTIALLY_FULFILLED = "PARTIALLY_FULFILLED"
    FULFILLED = "FULFILLED"
    CANCELLED = "CANCELLED"
    EXPIRED = "EXPIRED"


class NeedBase(BaseModel):
    meal_period: MealPeriod
    diet_type: DietType
    food_category_id: str = Field(..., description="ID of compatible food category")
    required_quantity_kg: float = Field(..., gt=0, description="Total required quantity in kg")
    minimum_quantity_kg: float = Field(..., gt=0, description="Minimum acceptable rescue batch quantity in kg")
    receiving_capacity_kg: float = Field(..., gt=0, description="Current physical storage/consumption capacity in kg")
    required_by: str = Field(..., description="ISO 8601 target delivery deadline")
    receiving_start_time: str = Field(default="08:00", description="HH:MM window start")
    receiving_end_time: str = Field(default="22:00", description="HH:MM window end")
    special_requirements: Optional[str] = None
    location_id: str = Field(..., description="Receiving center location UUID")

    @model_validator(mode="after")
    def validate_quantities(self) -> "NeedBase":
        if self.minimum_quantity_kg > self.required_quantity_kg:
            raise ValueError("minimum_quantity_kg cannot exceed required_quantity_kg.")
        if self.minimum_quantity_kg > self.receiving_capacity_kg:
            raise ValueError("minimum_quantity_kg cannot exceed receiving_capacity_kg.")
        return self


class NeedCreate(NeedBase):
    pass


class NeedUpdate(BaseModel):
    meal_period: Optional[MealPeriod] = None
    diet_type: Optional[DietType] = None
    food_category_id: Optional[str] = None
    required_quantity_kg: Optional[float] = Field(None, gt=0)
    minimum_quantity_kg: Optional[float] = Field(None, gt=0)
    receiving_capacity_kg: Optional[float] = Field(None, gt=0)
    required_by: Optional[str] = None
    receiving_start_time: Optional[str] = None
    receiving_end_time: Optional[str] = None
    special_requirements: Optional[str] = None
    location_id: Optional[str] = None


class NeedResponse(BaseModel):
    id: str
    receiver_id: str
    meal_period: MealPeriod
    diet_type: DietType
    food_category_id: str
    required_quantity_kg: float
    minimum_quantity_kg: float
    remaining_quantity_kg: float
    receiving_capacity_kg: float
    required_by: str
    receiving_start_time: str
    receiving_end_time: str
    special_requirements: Optional[str] = None
    location_id: str
    status: NeedStatus
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
