from datetime import date, datetime

from pydantic import BaseModel, Field, model_validator

from app.models.purchase import PurchaseOrderStatus


class ProductSupplierCreate(BaseModel):
    product_id: int
    supplier_code: str | None = None
    preferred: bool = False
    lead_time_days: int | None = Field(default=None, ge=0)


class ProductSupplierResponse(ProductSupplierCreate):
    id: int
    supplier_id: int
    supplier_name: str
    product_name: str
    last_price: float | None
    last_purchase_at: datetime | None


class PurchaseItemCreate(BaseModel):
    product_id: int
    quantity: float = Field(gt=0)
    unit_cost: float = Field(ge=0)
    notes: str | None = None


class PurchaseOrderCreate(BaseModel):
    supplier_id: int
    order_date: date = Field(default_factory=date.today)
    expected_date: date | None = None
    notes: str | None = None
    discount: float = Field(default=0, ge=0)
    status: PurchaseOrderStatus = PurchaseOrderStatus.WAITING
    items: list[PurchaseItemCreate]

    @model_validator(mode="after")
    def validate_items(self):
        if not self.items:
            raise ValueError("O pedido precisa ter ao menos um item.")
        return self


class PurchaseReceiptItemCreate(BaseModel):
    order_item_id: int
    quantity: float = Field(gt=0)
    unit_cost: float | None = Field(default=None, ge=0)
    lot_code: str | None = None
    expiration_date: date | None = None


class PurchaseReceiptCreate(BaseModel):
    items: list[PurchaseReceiptItemCreate]
    notes: str | None = None

    @model_validator(mode="after")
    def validate_items(self):
        if not self.items:
            raise ValueError("Informe ao menos um item recebido.")
        return self


class PurchaseItemResponse(BaseModel):
    id: int
    product_id: int
    product_name: str
    product_unit: str
    ordered_quantity: float
    received_quantity: float
    pending_quantity: float
    unit_cost: float
    subtotal: float
    notes: str | None


class PurchaseOrderResponse(BaseModel):
    id: int
    number: str
    supplier_id: int
    supplier_name: str
    created_by_name: str
    order_date: date
    expected_date: date | None
    notes: str | None
    subtotal: float
    discount: float
    total: float
    status: PurchaseOrderStatus
    created_at: datetime
    updated_at: datetime
    items: list[PurchaseItemResponse]


class PriceHistoryResponse(BaseModel):
    id: int
    supplier_id: int
    supplier_name: str
    product_id: int
    product_name: str
    unit_cost: float
    previous_cost: float | None
    variation_percent: float | None
    recorded_at: datetime
