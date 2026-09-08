from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class CategoryBase(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    description: str | None = None

    @field_validator("name")
    @classmethod
    def strip_name(cls, value: str) -> str:
        return value.strip()

    @field_validator("description", mode="before")
    @classmethod
    def empty_description_to_none(cls, value):
        return value.strip() or None if isinstance(value, str) else value


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(CategoryBase):
    pass


class CategoryResponse(CategoryBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
