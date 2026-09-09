from datetime import date, datetime

from pydantic import BaseModel, Field

from app.models.financial import FinancialCategoryType, FinancialStatus, RecurrenceFrequency
from app.models.sale import PaymentMethod


class FinancialCategoryCreate(BaseModel):
    name: str = Field(min_length=2, max_length=120)
    type: FinancialCategoryType
    affects_result: bool = True


class FinancialCategoryResponse(FinancialCategoryCreate):
    id: int
    active: bool


class PayableCreate(BaseModel):
    description: str = Field(min_length=2, max_length=200)
    category_id: int
    supplier_id: int | None = None
    purchase_order_id: int | None = None
    amount: float = Field(gt=0)
    due_date: date
    notes: str | None = None
    affects_result: bool | None = None


class FinancialPaymentCreate(BaseModel):
    amount: float = Field(gt=0)
    method: PaymentMethod
    occurred_at: datetime | None = None
    notes: str | None = None
    use_cash_register: bool = False
    idempotency_key: str | None = Field(default=None, min_length=8, max_length=80)


class FinancialPaymentResponse(BaseModel):
    id: int
    amount: float
    method: str
    user_name: str
    occurred_at: datetime
    notes: str | None


class PayableResponse(BaseModel):
    id: int
    description: str
    category_id: int
    category_name: str
    supplier_id: int | None
    supplier_name: str | None
    purchase_order_id: int | None
    original_amount: float
    paid_amount: float
    balance: float
    due_date: date
    paid_at: datetime | None
    status: str
    is_overdue: bool
    payment_method: str | None
    notes: str | None
    origin: str
    affects_result: bool
    created_at: datetime
    payments: list[FinancialPaymentResponse] = Field(default_factory=list)


class ManualRevenueCreate(BaseModel):
    description: str = Field(min_length=2, max_length=200)
    category_id: int
    amount: float = Field(gt=0)
    received_at: datetime | None = None
    competence_date: date | None = None
    payment_method: PaymentMethod
    reference: str | None = None
    notes: str | None = None
    idempotency_key: str | None = Field(default=None, min_length=8, max_length=80)


class ManualRevenueResponse(BaseModel):
    id: int
    description: str
    category_name: str
    amount: float
    received_at: datetime
    competence_date: date | None
    payment_method: str
    reference: str | None
    notes: str | None
    cancelled: bool
    created_by_name: str


class ReceivableCreate(BaseModel):
    description: str = Field(min_length=2, max_length=200)
    category_id: int
    customer_id: int | None = None
    amount: float = Field(gt=0)
    due_date: date
    notes: str | None = None


class ReceivableResponse(BaseModel):
    id: str
    source_id: int
    source: str
    description: str
    customer_id: int | None
    customer_name: str | None
    original_amount: float
    received_amount: float
    balance: float
    due_date: date | None
    status: str
    is_overdue: bool
    created_at: datetime


class RecurringExpenseCreate(BaseModel):
    description: str = Field(min_length=2, max_length=200)
    category_id: int
    supplier_id: int | None = None
    amount: float = Field(gt=0)
    frequency: RecurrenceFrequency
    next_due_date: date
    notes: str | None = None


class RecurringExpenseResponse(RecurringExpenseCreate):
    id: int
    active: bool
    created_at: datetime


class CashFlowEntry(BaseModel):
    id: str
    occurred_at: datetime
    direction: str
    source: str
    description: str
    amount: float
    payment_method: str


class FinancialSummaryResponse(BaseModel):
    period_start: date
    period_end: date
    revenue: float
    sales_count: int
    average_ticket: float
    received_sales: float
    credit_sales: float
    credit_receipts: float
    manual_revenues: float
    cash_in: float
    cmv: float
    gross_profit: float
    gross_margin: float
    operational_expenses: float
    cash_out: float
    estimated_result: float
    payables_balance: float
    receivables_balance: float
    overdue_payables: float
    overdue_receivables: float
    payment_methods: dict[str, float]


class ProjectionResponse(BaseModel):
    days: int
    payables: float
    receivables: float


class ReconciliationIssue(BaseModel):
    code: str
    description: str
    reference_id: int | None = None
    severity: str
