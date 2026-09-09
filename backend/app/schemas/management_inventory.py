from datetime import date, datetime

from pydantic import BaseModel, Field, model_validator

from app.models.management_inventory import InventoryCountStatus, LossReason, LotStatus


class LotCreate(BaseModel):
    product_id: int
    supplier_id: int | None = None
    lot_code: str | None = None
    quantity: float = Field(gt=0)
    unit_cost: float = Field(default=0, ge=0)
    entry_date: date = Field(default_factory=date.today)
    expiration_date: date | None = None
    add_to_stock: bool = True


class LotResponse(BaseModel):
    id: int
    product_id: int
    product_name: str
    supplier_name: str | None
    lot_code: str | None
    initial_quantity: float
    current_quantity: float
    unit_cost: float
    entry_date: date
    expiration_date: date | None
    expiry_state: str
    days_remaining: int | None
    status: LotStatus
    created_at: datetime


class LossCreate(BaseModel):
    product_id: int
    lot_id: int | None = None
    quantity: float = Field(gt=0)
    reason: LossReason
    notes: str | None = None


class LossResponse(BaseModel):
    id: int
    product_name: str
    lot_code: str | None
    quantity: float
    reason: LossReason
    notes: str | None
    user_name: str
    created_at: datetime


class InventoryCountCreate(BaseModel):
    category_id: int | None = None
    product_ids: list[int] = Field(default_factory=list)
    notes: str | None = None


class InventoryCountValue(BaseModel):
    product_id: int
    counted_quantity: float = Field(ge=0)


class InventoryCountComplete(BaseModel):
    items: list[InventoryCountValue]

    @model_validator(mode="after")
    def validate_items(self):
        if not self.items:
            raise ValueError("Informe as quantidades contadas.")
        return self


class InventoryCountItemResponse(BaseModel):
    id: int
    product_id: int
    product_name: str
    system_quantity: float
    counted_quantity: float | None
    difference: float | None


class InventoryCountResponse(BaseModel):
    id: int
    number: str
    responsible_name: str
    category_name: str | None
    notes: str | None
    status: InventoryCountStatus
    created_at: datetime
    completed_at: datetime | None
    positive_differences: float
    negative_differences: float
    items: list[InventoryCountItemResponse]
