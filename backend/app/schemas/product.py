from datetime import datetime

from pydantic import BaseModel, Field, computed_field


class ProductBase(BaseModel):
    name: str
    description: str | None = None
    sku: str
    barcode: str | None = None
    category_id: int | None = None
    supplier_id: int | None = None
    cost_price: float = Field(ge=0)
    sale_price: float = Field(ge=0)
    stock_quantity: float = Field(ge=0)
    minimum_stock: float = Field(ge=0)
    unit: str
    active: bool = True


class ProductCreate(ProductBase):
    pass


class ProductUpdate(ProductBase):
    pass


class ProductResponse(ProductBase):
    id: int
    created_at: datetime
    updated_at: datetime
    category_name: str | None = None
    supplier_name: str | None = None

    @computed_field
    @property
    def margin(self) -> float:
        return round(self.sale_price - self.cost_price, 2)

    @computed_field
    @property
    def margin_percent(self) -> float:
        if self.cost_price == 0:
            return 0
        return round(((self.sale_price - self.cost_price) / self.cost_price) * 100, 2)

    @computed_field
    @property
    def stock_status(self) -> str:
        if self.stock_quantity <= 0:
            return "SEM ESTOQUE"
        if self.stock_quantity <= self.minimum_stock * 0.5:
            return "CRÍTICO"
        if self.stock_quantity <= self.minimum_stock:
            return "BAIXO"
        return "NORMAL"

    class Config:
        from_attributes = True
