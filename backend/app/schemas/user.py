from datetime import datetime

from pydantic import BaseModel, EmailStr, Field

from app.models.user import UserRole


class UserCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=6, max_length=120)
    role: UserRole
    active: bool = True


class UserUpdate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    role: UserRole
    active: bool = True
    password: str | None = Field(default=None, min_length=6, max_length=120)


class UserResponse(BaseModel):
    id: int
    name: str
    # Legacy installations may contain local development domains.
    email: str
    role: UserRole
    profile_name: str
    active: bool
    created_at: datetime
