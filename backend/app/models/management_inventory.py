import enum
from datetime import date, datetime

from sqlalchemy import Date, DateTime, Enum, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base


class LotStatus(str, enum.Enum):
    AVAILABLE = "DISPONIVEL"
    DEPLETED = "ESGOTADO"


class LossReason(str, enum.Enum):
    EXPIRED = "VENCIDO"
    DAMAGED = "DANIFICADO"
    BREAKAGE = "QUEBRA"
    INTERNAL_USE = "CONSUMO_INTERNO"
    THEFT = "FURTO"
    OTHER = "OUTRO"


class InventoryCountStatus(str, enum.Enum):
    IN_PROGRESS = "EM_ANDAMENTO"
    COMPLETED = "CONCLUIDO"
    CANCELLED = "CANCELADO"


class ProductLot(Base):
    __tablename__ = "product_lots"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"), nullable=False, index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False, index=True)
    supplier_id: Mapped[int | None] = mapped_column(ForeignKey("suppliers.id"), nullable=True)
    receipt_id: Mapped[int | None] = mapped_column(ForeignKey("purchase_receipts.id"), nullable=True)
    lot_code: Mapped[str | None] = mapped_column(String(100), nullable=True)
    initial_quantity: Mapped[float] = mapped_column(Numeric(12, 3), nullable=False)
    current_quantity: Mapped[float] = mapped_column(Numeric(12, 3), nullable=False)
    unit_cost: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    entry_date: Mapped[date] = mapped_column(Date, default=date.today, nullable=False)
    expiration_date: Mapped[date | None] = mapped_column(Date, nullable=True, index=True)
    status: Mapped[LotStatus] = mapped_column(Enum(LotStatus), default=LotStatus.AVAILABLE, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    product = relationship("Product", back_populates="lots")
    supplier = relationship("Supplier")
    receipt = relationship("PurchaseReceipt")
    losses = relationship("InventoryLoss", back_populates="lot")


class InventoryLoss(Base):
    __tablename__ = "inventory_losses"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"), nullable=False, index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    lot_id: Mapped[int | None] = mapped_column(ForeignKey("product_lots.id"), nullable=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    quantity: Mapped[float] = mapped_column(Numeric(12, 3), nullable=False)
    reason: Mapped[LossReason] = mapped_column(Enum(LossReason), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    product = relationship("Product")
    lot = relationship("ProductLot", back_populates="losses")
    user = relationship("User")


class InventoryCount(Base):
    __tablename__ = "inventory_counts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"), nullable=False, index=True)
    created_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    category_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id"), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[InventoryCountStatus] = mapped_column(Enum(InventoryCountStatus), default=InventoryCountStatus.IN_PROGRESS, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_by = relationship("User")
    category = relationship("Category")
    items = relationship("InventoryCountItem", back_populates="inventory", cascade="all, delete-orphan")


class InventoryCountItem(Base):
    __tablename__ = "inventory_count_items"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    inventory_id: Mapped[int] = mapped_column(ForeignKey("inventory_counts.id"), nullable=False, index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    system_quantity: Mapped[float] = mapped_column(Numeric(12, 3), nullable=False)
    counted_quantity: Mapped[float | None] = mapped_column(Numeric(12, 3), nullable=True)
    difference: Mapped[float | None] = mapped_column(Numeric(12, 3), nullable=True)
    inventory = relationship("InventoryCount", back_populates="items")
    product = relationship("Product")
