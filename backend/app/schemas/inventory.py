from datetime import datetime

from pydantic import BaseModel, Field

from app.models.stock_movement import StockMovementType


class InventoryRecord(BaseModel):
    product_id: int
    product_name: str
    sku: str
    category_name: str | None
    stock_quantity: float
    minimum_stock: float
    average_sales_per_day: float
    days_remaining: float | None
    purchase_recommendation: float
    status: str


class StockAlert(BaseModel):
    product_id: int
    product_name: str
    stock_quantity: float
    minimum_stock: float
    status: str


class StockMovementCreate(BaseModel):
    product_id: int
    quantity: float = Field(gt=0)
    type: StockMovementType
    reason: str | None = None


class StockMovementResponse(BaseModel):
    id: int
    product_name: str
    quantity: float
    previous_stock: float
    new_stock: float
    type: StockMovementType
    user_name: str | None
    reason: str | None
    created_at: datetime
