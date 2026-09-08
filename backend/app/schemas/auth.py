from datetime import datetime

from pydantic import BaseModel, EmailStr

from app.schemas.account import AccountResponse
from app.models.user import UserRole


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class CurrentUserResponse(BaseModel):
    id: int
    account_id: int
    name: str
    email: EmailStr
    role: UserRole
    active: bool
    created_at: datetime
    account: AccountResponse

    class Config:
        from_attributes = True
