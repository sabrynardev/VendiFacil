from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.schemas.account import AccountResponse
from app.models.user import UserRole


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class CurrentUserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    account_id: int
    name: str
    email: str
    role: UserRole
    active: bool
    created_at: datetime
    account: AccountResponse
    profile_name: str
    permissions: list[str]
