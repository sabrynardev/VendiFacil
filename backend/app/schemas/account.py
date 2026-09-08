from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class AccountResponse(BaseModel):
    id: int
    name: str
    active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class AccountRegisterRequest(BaseModel):
    account_name: str = Field(min_length=2, max_length=160)
    admin_name: str = Field(min_length=2, max_length=120)
    admin_email: EmailStr
    password: str = Field(min_length=6, max_length=120)
    with_default_categories: bool = True
