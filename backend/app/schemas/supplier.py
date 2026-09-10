from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr


class SupplierBase(BaseModel):
    name: str
    trade_name: str | None = None
    cnpj: str | None = None
    phone: str | None = None
    whatsapp: str | None = None
    email: EmailStr | None = None
    address: str | None = None
    city: str | None = None
    state: str | None = None
    notes: str | None = None
    active: bool = True


class SupplierCreate(SupplierBase):
    pass


class SupplierUpdate(SupplierBase):
    pass


class SupplierResponse(SupplierBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    # Instalações antigas podem conter domínios locais usados nos dados de demonstração.
    email: str | None = None
    created_at: datetime
    updated_at: datetime
    products_count: int = 0
