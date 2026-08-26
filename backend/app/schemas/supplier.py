from datetime import datetime

from pydantic import BaseModel, EmailStr


class SupplierBase(BaseModel):
    name: str
    cnpj: str | None = None
    phone: str | None = None
    whatsapp: str | None = None
    email: EmailStr | None = None
    address: str | None = None
    notes: str | None = None


class SupplierCreate(SupplierBase):
    pass


class SupplierUpdate(SupplierBase):
    pass


class SupplierResponse(SupplierBase):
    id: int
    created_at: datetime
    products_count: int = 0

    class Config:
        from_attributes = True
