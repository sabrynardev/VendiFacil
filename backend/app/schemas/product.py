from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator, model_validator

from app.core.products import ProductUnit, calculate_margin


class ProductBase(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    brand: str | None = Field(default=None, max_length=100)
    description: str | None = None
    sku: str = Field(min_length=1, max_length=60)
    barcode: str | None = Field(default=None, max_length=60)
    category_id: int | None = None
    supplier_id: int | None = None
    cost_price: float = Field(ge=0)
    sale_price: float = Field(ge=0)
    stock_quantity: float = Field(ge=0)
    minimum_stock: float = Field(ge=0)
    unit: ProductUnit = ProductUnit.UN
    active: bool = True

    @field_validator("name", "sku")
    @classmethod
    def strip_required_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Este campo não pode ficar vazio.")
        return value

    @field_validator("brand", "description", "barcode", mode="before")
    @classmethod
    def empty_text_to_none(cls, value):
        return value.strip() or None if isinstance(value, str) else value

    @model_validator(mode="after")
    def validate_unit_quantities(self):
        if self.unit == ProductUnit.UN and (not float(self.stock_quantity).is_integer() or not float(self.minimum_stock).is_integer()):
            raise ValueError("Produtos por unidade devem usar estoque em números inteiros.")
        return self


class ProductCreate(ProductBase):
    pass


class ProductUpdate(ProductBase):
    pass


class ProductResponse(ProductBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
    category_name: str | None = None
    supplier_name: str | None = None

    @computed_field
    @property
    def margin(self) -> float:
        return calculate_margin(self.cost_price, self.sale_price)[0]

    @computed_field
    @property
    def margin_percent(self) -> float:
        return calculate_margin(self.cost_price, self.sale_price)[1]

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
