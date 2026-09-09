import enum
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base


class DebtStatus(str, enum.Enum):
    OPEN = "EM_ABERTO"
    PARTIAL = "PARCIAL"
    PAID = "QUITADO"
    REVERSED = "ESTORNADO"


class Customer(Base):
    __tablename__ = "customers"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    phone: Mapped[str | None] = mapped_column(String(30), nullable=True)
    whatsapp: Mapped[str | None] = mapped_column(String(30), nullable=True)
    cpf: Mapped[str | None] = mapped_column(String(14), nullable=True)
    address: Mapped[str | None] = mapped_column(Text, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    credit_limit: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    credit_blocked: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    sales = relationship("Sale", back_populates="customer", foreign_keys="Sale.customer_id")
    debts = relationship("CustomerDebt", back_populates="customer")
    payments = relationship("CustomerPayment", back_populates="customer")


class CustomerDebt(Base):
    __tablename__ = "customer_debts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"), nullable=False, index=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), nullable=False, index=True)
    sale_id: Mapped[int] = mapped_column(ForeignKey("sales.id"), nullable=False, unique=True)
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    balance: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    status: Mapped[DebtStatus] = mapped_column(Enum(DebtStatus), default=DebtStatus.OPEN, nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    customer = relationship("Customer", back_populates="debts")
    sale = relationship("Sale", back_populates="customer_debt")
    allocations = relationship("CustomerPaymentAllocation", back_populates="debt")


class CustomerPayment(Base):
    __tablename__ = "customer_payments"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"), nullable=False, index=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("customers.id"), nullable=False, index=True)
    received_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    method: Mapped[str] = mapped_column(String(20), nullable=False)
    balance_before: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    balance_after: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    customer = relationship("Customer", back_populates="payments")
    received_by = relationship("User")
    allocations = relationship("CustomerPaymentAllocation", back_populates="payment", cascade="all, delete-orphan")


class CustomerPaymentAllocation(Base):
    __tablename__ = "customer_payment_allocations"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    payment_id: Mapped[int] = mapped_column(ForeignKey("customer_payments.id"), nullable=False, index=True)
    debt_id: Mapped[int] = mapped_column(ForeignKey("customer_debts.id"), nullable=False, index=True)
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    payment = relationship("CustomerPayment", back_populates="allocations")
    debt = relationship("CustomerDebt", back_populates="allocations")
