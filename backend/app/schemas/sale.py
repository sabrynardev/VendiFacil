from datetime import date, datetime

from pydantic import BaseModel, Field, model_validator

from app.models.sale import PaymentMethod, SaleStatus


class SaleItemCreate(BaseModel):
    product_id: int
    quantity: float = Field(gt=0)
    discount: float = Field(ge=0, default=0)


class PaymentCreate(BaseModel):
    method: PaymentMethod
    amount: float = Field(gt=0)
    amount_received: float | None = Field(default=None, ge=0)


class SaleCreate(BaseModel):
    items: list[SaleItemCreate]
    discount: float = Field(ge=0, default=0)
    surcharge: float = Field(ge=0, default=0)
    payments: list[PaymentCreate] = Field(default_factory=list)
    payment_method: PaymentMethod | None = None
    amount_received: float | None = Field(default=None, ge=0)
    note: str | None = Field(default=None, max_length=500)
    idempotency_key: str | None = Field(default=None, min_length=8, max_length=80)
    authorization_email: str | None = None
    authorization_password: str | None = None
    customer_id: int | None = None
    credit_due_date: date | None = None

    @model_validator(mode="after")
    def validate_items(self):
        if not self.items:
            raise ValueError("A venda precisa ter ao menos um item.")
        if not self.payments and not self.payment_method:
            raise ValueError("Informe ao menos uma forma de pagamento.")
        return self


class HoldSaleCreate(BaseModel):
    items: list[SaleItemCreate]
    discount: float = Field(ge=0, default=0)
    surcharge: float = Field(ge=0, default=0)
    note: str | None = Field(default=None, max_length=500)
    customer_id: int | None = None

    @model_validator(mode="after")
    def validate_items(self):
        if not self.items:
            raise ValueError("A venda em espera precisa ter ao menos um item.")
        return self


class SaleCancel(BaseModel):
    reason: str = Field(min_length=3, max_length=500)


class SaleItemResponse(BaseModel):
    id: int
    product_id: int
    product_name: str
    product_unit: str
    quantity: float
    unit_price: float
    discount: float
    subtotal: float


class PaymentResponse(BaseModel):
    id: int
    method: PaymentMethod
    amount: float
    amount_received: float | None
    change_amount: float


class SaleResponse(BaseModel):
    id: int
    number: str
    user_id: int
    operator_name: str
    cash_register_id: int | None
    customer_id: int | None
    customer_name: str | None
    credit_due_date: date | None
    subtotal: float
    discount: float
    surcharge: float
    total: float
    payment_method: str
    amount_received: float | None
    change_amount: float | None
    status: SaleStatus
    note: str | None
    cancellation_reason: str | None
    cancelled_at: datetime | None
    created_at: datetime
    items: list[SaleItemResponse]
    payments: list[PaymentResponse]


class OfflineSaleItem(BaseModel):
    product_id: int
    quantity: float = Field(gt=0)
    unit_price: float = Field(ge=0)
    discount: float = Field(ge=0, default=0)
    product_updated_at: datetime | None = None


class OfflineSaleCreate(BaseModel):
    operation_id: str = Field(min_length=16, max_length=80)
    idempotency_key: str = Field(min_length=16, max_length=80)
    device_id: str = Field(min_length=8, max_length=80)
    local_created_at: datetime
    cash_register_id: int | None = None
    items: list[OfflineSaleItem] = Field(min_length=1)
    discount: float = Field(ge=0, default=0)
    surcharge: float = Field(ge=0, default=0)
    payments: list[PaymentCreate] = Field(min_length=1)
    note: str | None = Field(default=None, max_length=500)


class SyncResult(BaseModel):
    operation_id: str
    status: str
    duplicate: bool = False
    conflict: bool = False
    conflicts: list[str] = Field(default_factory=list)
    sale: SaleResponse | None = None
