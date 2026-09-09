import enum
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base


class FinancialCategoryType(str, enum.Enum):
    REVENUE = "RECEITA"
    EXPENSE = "DESPESA"


class FinancialStatus(str, enum.Enum):
    PENDING = "PENDENTE"
    PARTIAL = "PARCIAL"
    PAID = "PAGA"
    CANCELLED = "CANCELADA"


class FinancialOrigin(str, enum.Enum):
    MANUAL = "MANUAL"
    PURCHASE = "COMPRA"
    RECURRING = "RECORRENTE"


class RecurrenceFrequency(str, enum.Enum):
    WEEKLY = "SEMANAL"
    MONTHLY = "MENSAL"
    YEARLY = "ANUAL"


class FinancialCategory(Base):
    __tablename__ = "financial_categories"
    __table_args__ = (UniqueConstraint("account_id", "type", "name", name="uq_financial_category_name"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    type: Mapped[FinancialCategoryType] = mapped_column(Enum(FinancialCategoryType), nullable=False)
    affects_result: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)


class Payable(Base):
    __tablename__ = "payables"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"), nullable=False, index=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("financial_categories.id"), nullable=False)
    supplier_id: Mapped[int | None] = mapped_column(ForeignKey("suppliers.id"), nullable=True)
    purchase_order_id: Mapped[int | None] = mapped_column(ForeignKey("purchase_orders.id"), nullable=True, unique=True)
    created_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    description: Mapped[str] = mapped_column(String(200), nullable=False)
    original_amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    paid_amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    paid_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    status: Mapped[FinancialStatus] = mapped_column(Enum(FinancialStatus), default=FinancialStatus.PENDING, nullable=False)
    payment_method: Mapped[str | None] = mapped_column(String(30), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    origin: Mapped[FinancialOrigin] = mapped_column(Enum(FinancialOrigin), default=FinancialOrigin.MANUAL, nullable=False)
    reference: Mapped[str | None] = mapped_column(String(100), nullable=True)
    affects_result: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    recurrence_id: Mapped[int | None] = mapped_column(ForeignKey("recurring_expenses.id"), nullable=True)
    recurrence_period: Mapped[str | None] = mapped_column(String(20), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    category = relationship("FinancialCategory")
    supplier = relationship("Supplier")
    purchase_order = relationship("PurchaseOrder")
    created_by = relationship("User")
    payments = relationship("PayablePayment", back_populates="payable")
    recurrence = relationship("RecurringExpense", back_populates="generated_payables")


class PayablePayment(Base):
    __tablename__ = "payable_payments"
    __table_args__ = (UniqueConstraint("account_id", "idempotency_key", name="uq_payable_payment_idempotency"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"), nullable=False, index=True)
    payable_id: Mapped[int] = mapped_column(ForeignKey("payables.id"), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    cash_register_id: Mapped[int | None] = mapped_column(ForeignKey("cash_registers.id"), nullable=True)
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    method: Mapped[str] = mapped_column(String(30), nullable=False)
    payment_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    idempotency_key: Mapped[str | None] = mapped_column(String(80), nullable=True)

    payable = relationship("Payable", back_populates="payments")
    user = relationship("User")
    cash_register = relationship("CashRegister")


class ManualRevenue(Base):
    __tablename__ = "manual_revenues"
    __table_args__ = (UniqueConstraint("account_id", "idempotency_key", name="uq_manual_revenue_idempotency"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"), nullable=False, index=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("financial_categories.id"), nullable=False)
    created_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    description: Mapped[str] = mapped_column(String(200), nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    received_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    competence_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    payment_method: Mapped[str] = mapped_column(String(30), nullable=False)
    reference: Mapped[str | None] = mapped_column(String(100), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    idempotency_key: Mapped[str | None] = mapped_column(String(80), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    category = relationship("FinancialCategory")
    created_by = relationship("User")


class FinancialReceivable(Base):
    __tablename__ = "financial_receivables"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"), nullable=False, index=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("financial_categories.id"), nullable=False)
    customer_id: Mapped[int | None] = mapped_column(ForeignKey("customers.id"), nullable=True)
    created_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    description: Mapped[str] = mapped_column(String(200), nullable=False)
    original_amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    received_amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    due_date: Mapped[date] = mapped_column(Date, nullable=False)
    status: Mapped[FinancialStatus] = mapped_column(Enum(FinancialStatus), default=FinancialStatus.PENDING, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    category = relationship("FinancialCategory")
    customer = relationship("Customer")
    created_by = relationship("User")
    receipts = relationship("ReceivableReceipt", back_populates="receivable")


class ReceivableReceipt(Base):
    __tablename__ = "receivable_receipts"
    __table_args__ = (UniqueConstraint("account_id", "idempotency_key", name="uq_receivable_receipt_idempotency"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"), nullable=False, index=True)
    receivable_id: Mapped[int] = mapped_column(ForeignKey("financial_receivables.id"), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    method: Mapped[str] = mapped_column(String(30), nullable=False)
    received_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    idempotency_key: Mapped[str | None] = mapped_column(String(80), nullable=True)

    receivable = relationship("FinancialReceivable", back_populates="receipts")
    user = relationship("User")


class RecurringExpense(Base):
    __tablename__ = "recurring_expenses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"), nullable=False, index=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("financial_categories.id"), nullable=False)
    supplier_id: Mapped[int | None] = mapped_column(ForeignKey("suppliers.id"), nullable=True)
    created_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    description: Mapped[str] = mapped_column(String(200), nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    frequency: Mapped[RecurrenceFrequency] = mapped_column(Enum(RecurrenceFrequency), nullable=False)
    next_due_date: Mapped[date] = mapped_column(Date, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    category = relationship("FinancialCategory")
    supplier = relationship("Supplier")
    created_by = relationship("User")
    generated_payables = relationship("Payable", back_populates="recurrence")
