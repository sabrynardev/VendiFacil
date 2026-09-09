import enum
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base


class SaleStatus(str, enum.Enum):
    ON_HOLD = "ON_HOLD"
    COMPLETED = "COMPLETED"
    CANCELLED = "CANCELLED"


class PaymentMethod(str, enum.Enum):
    CASH = "DINHEIRO"
    PIX = "PIX"
    DEBIT = "DEBITO"
    CREDIT = "CREDITO"
    CREDIT_ACCOUNT = "FIADO"


class Sale(Base):
    __tablename__ = "sales"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    cash_register_id: Mapped[int | None] = mapped_column(ForeignKey("cash_registers.id"), nullable=True, index=True)
    customer_id: Mapped[int | None] = mapped_column(ForeignKey("customers.id"), nullable=True, index=True)
    subtotal: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    discount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    surcharge: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    total: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    payment_method: Mapped[str] = mapped_column(String(30), nullable=False, default="PENDENTE")
    amount_received: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    change_amount: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    status: Mapped[SaleStatus] = mapped_column(Enum(SaleStatus), nullable=False, default=SaleStatus.COMPLETED)
    note: Mapped[str | None] = mapped_column(String(500), nullable=True)
    idempotency_key: Mapped[str | None] = mapped_column(String(80), nullable=True, index=True)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    cancelled_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    cancellation_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    credit_due_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    credit_authorized_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    account = relationship("Account")
    user = relationship("User", foreign_keys=[user_id])
    cash_register = relationship("CashRegister", back_populates="sales")
    cancelled_by = relationship("User", foreign_keys=[cancelled_by_id])
    credit_authorized_by = relationship("User", foreign_keys=[credit_authorized_by_id])
    customer = relationship("Customer", back_populates="sales", foreign_keys=[customer_id])
    customer_debt = relationship("CustomerDebt", back_populates="sale", uselist=False)
    items = relationship("SaleItem", back_populates="sale", cascade="all, delete-orphan")
    payments = relationship("SalePayment", back_populates="sale", cascade="all, delete-orphan")


class SaleItem(Base):
    __tablename__ = "sale_items"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    sale_id: Mapped[int] = mapped_column(ForeignKey("sales.id"), nullable=False)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    quantity: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    unit_price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    discount: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False, default=0)
    subtotal: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)

    sale = relationship("Sale", back_populates="items")
    product = relationship("Product", back_populates="sale_items")


class SalePayment(Base):
    __tablename__ = "sale_payments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    sale_id: Mapped[int] = mapped_column(ForeignKey("sales.id"), nullable=False, index=True)
    method: Mapped[PaymentMethod] = mapped_column(Enum(PaymentMethod), nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    amount_received: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    change_amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    confirmed_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    sale = relationship("Sale", back_populates="payments")
