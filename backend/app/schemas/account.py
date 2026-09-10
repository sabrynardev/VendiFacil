from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class AccountResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    active: bool
    created_at: datetime

class AccountRegisterRequest(BaseModel):
    account_name: str = Field(min_length=2, max_length=160)
    admin_name: str = Field(min_length=2, max_length=120)
    admin_email: EmailStr
    password: str = Field(min_length=6, max_length=120)
    with_default_categories: bool = True
