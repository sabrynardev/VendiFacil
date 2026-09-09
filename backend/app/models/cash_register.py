import enum
from datetime import datetime

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base


class CashRegisterStatus(str, enum.Enum):
    OPEN = "OPEN"
    CLOSED = "CLOSED"


class CashMovementType(str, enum.Enum):
    OPENING = "OPENING"
    SALE = "SALE"
    WITHDRAWAL = "WITHDRAWAL"
    SUPPLY = "SUPPLY"
    REFUND = "REFUND"
    CLOSING = "CLOSING"
    CREDIT_RECEIPT = "RECEBIMENTO_FIADO"


class CashRegister(Base):
    __tablename__ = "cash_registers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"), nullable=False, index=True)
    opened_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    closed_by_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    opened_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    closed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    opening_balance: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    expected_balance: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    counted_balance: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    difference: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    status: Mapped[CashRegisterStatus] = mapped_column(Enum(CashRegisterStatus), default=CashRegisterStatus.OPEN, nullable=False)
    closing_note: Mapped[str | None] = mapped_column(Text, nullable=True)

    opened_by = relationship("User", foreign_keys=[opened_by_id])
    closed_by = relationship("User", foreign_keys=[closed_by_id])
    movements = relationship("CashMovement", back_populates="cash_register")
    sales = relationship("Sale", back_populates="cash_register")


class CashMovement(Base):
    __tablename__ = "cash_movements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"), nullable=False, index=True)
    cash_register_id: Mapped[int] = mapped_column(ForeignKey("cash_registers.id"), nullable=False, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    type: Mapped[CashMovementType] = mapped_column(Enum(CashMovementType), nullable=False)
    amount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    payment_method: Mapped[str | None] = mapped_column(String(20), nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    reference_type: Mapped[str | None] = mapped_column(String(40), nullable=True)
    reference_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    cash_register = relationship("CashRegister", back_populates="movements")
    user = relationship("User")
