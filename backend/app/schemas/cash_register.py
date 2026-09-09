from datetime import datetime

from pydantic import BaseModel, Field

from app.models.cash_register import CashMovementType, CashRegisterStatus


class CashRegisterOpen(BaseModel):
    opening_balance: float = Field(ge=0)


class CashMovementCreate(BaseModel):
    amount: float = Field(gt=0)
    reason: str = Field(min_length=3, max_length=500)


class CashRegisterClose(BaseModel):
    counted_balance: float = Field(ge=0)
    note: str | None = Field(default=None, max_length=500)


class CashMovementResponse(BaseModel):
    id: int
    type: CashMovementType
    amount: float
    payment_method: str | None
    reason: str | None
    user_name: str
    reference_type: str | None
    reference_id: int | None
    created_at: datetime


class CashSummary(BaseModel):
    opening_balance: float
    cash_sales: float
    pix_sales: float
    debit_sales: float
    credit_sales: float
    total_sales: float
    supplies: float
    withdrawals: float
    refunds: float
    expected_cash: float


class CashRegisterResponse(BaseModel):
    id: int
    operator_name: str
    closed_by_name: str | None
    opened_at: datetime
    closed_at: datetime | None
    opening_balance: float
    expected_balance: float | None
    counted_balance: float | None
    difference: float | None
    status: CashRegisterStatus
    closing_note: str | None
    summary: CashSummary
    movements: list[CashMovementResponse] = []
