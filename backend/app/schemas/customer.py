from datetime import date, datetime

from pydantic import BaseModel, Field

from app.models.customer import DebtStatus
from app.models.sale import PaymentMethod


class CustomerBase(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    phone: str | None = None
    whatsapp: str | None = None
    cpf: str | None = None
    address: str | None = None
    notes: str | None = None
    credit_limit: float | None = Field(default=None, ge=0)
    credit_blocked: bool = False
    active: bool = True


class CustomerCreate(CustomerBase):
    pass


class CustomerUpdate(CustomerBase):
    pass


class CustomerDebtResponse(BaseModel):
    id: int
    sale_id: int
    sale_number: str
    amount: float
    balance: float
    due_date: date | None
    status: DebtStatus
    is_overdue: bool
    days_open: int
    created_at: datetime


class CustomerPaymentCreate(BaseModel):
    amount: float = Field(gt=0)
    method: PaymentMethod
    notes: str | None = None


class CustomerPaymentResponse(BaseModel):
    id: int
    amount: float
    method: str
    responsible_name: str
    balance_before: float
    balance_after: float
    notes: str | None
    created_at: datetime


class CustomerSaleResponse(BaseModel):
    id: int
    number: str
    total: float
    payment_method: str
    status: str
    created_at: datetime


class CustomerResponse(CustomerBase):
    id: int
    balance: float
    available_credit: float | None
    total_purchased: float
    ticket_average: float
    last_purchase_at: datetime | None
    overdue_balance: float
    created_at: datetime
    updated_at: datetime
    debts: list[CustomerDebtResponse] = Field(default_factory=list)
    payments: list[CustomerPaymentResponse] = Field(default_factory=list)
    sales: list[CustomerSaleResponse] = Field(default_factory=list)


class CreditAuthorization(BaseModel):
    authorization_email: str | None = None
    authorization_password: str | None = None
