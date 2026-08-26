from datetime import datetime

from pydantic import BaseModel, Field, model_validator

from app.models.sale import SaleStatus


class SaleItemCreate(BaseModel):
    product_id: int
    quantity: float = Field(gt=0)
    discount: float = Field(ge=0, default=0)


class SaleCreate(BaseModel):
    items: list[SaleItemCreate]
    discount: float = Field(ge=0, default=0)
    payment_method: str
    amount_received: float | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def validate_items(self):
        if not self.items:
            raise ValueError("A venda precisa ter ao menos um item.")
        return self


class SaleItemResponse(BaseModel):
    id: int
    product_id: int
    product_name: str
    quantity: float
    unit_price: float
    discount: float
    subtotal: float


class SaleResponse(BaseModel):
    id: int
    user_id: int
    operator_name: str
    subtotal: float
    discount: float
    total: float
    payment_method: str
    amount_received: float | None
    change_amount: float | None
    status: SaleStatus
    created_at: datetime
    items: list[SaleItemResponse]
