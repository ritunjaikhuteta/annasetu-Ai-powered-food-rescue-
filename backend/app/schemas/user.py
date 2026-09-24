"""User schemas."""

from typing import Optional
from pydantic import BaseModel, EmailStr
from app.schemas.common import UserRole


class UserResponse(BaseModel):
    """User summary response model."""

    id: str
    email: Optional[EmailStr] = None
    role: UserRole
    full_name: Optional[str] = None
    is_active: bool = True
