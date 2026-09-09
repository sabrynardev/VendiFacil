import enum
from datetime import date, datetime

from sqlalchemy import Boolean, Date, DateTime, Enum, ForeignKey, Integer, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.session import Base


class PurchaseOrderStatus(str, enum.Enum):
    DRAFT = "RASCUNHO"
    SENT = "ENVIADO"
    WAITING = "AGUARDANDO"
    PARTIALLY_RECEIVED = "PARCIALMENTE_RECEBIDO"
    RECEIVED = "RECEBIDO"
    CANCELLED = "CANCELADO"


class ProductSupplier(Base):
    __tablename__ = "product_suppliers"
    __table_args__ = (UniqueConstraint("account_id", "product_id", "supplier_id", name="uq_product_supplier"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"), nullable=False, index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False, index=True)
    supplier_id: Mapped[int] = mapped_column(ForeignKey("suppliers.id"), nullable=False, index=True)
    supplier_code: Mapped[str | None] = mapped_column(String(80), nullable=True)
    last_price: Mapped[float | None] = mapped_column(Numeric(12, 2), nullable=True)
    last_purchase_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    preferred: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    lead_time_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    product = relationship("Product", back_populates="supplier_links")
    supplier = relationship("Supplier", back_populates="product_links")


class PurchaseOrder(Base):
    __tablename__ = "purchase_orders"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"), nullable=False, index=True)
    supplier_id: Mapped[int] = mapped_column(ForeignKey("suppliers.id"), nullable=False)
    created_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    order_date: Mapped[date] = mapped_column(Date, default=date.today, nullable=False)
    expected_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    subtotal: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    discount: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    total: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False, default=0)
    status: Mapped[PurchaseOrderStatus] = mapped_column(Enum(PurchaseOrderStatus), default=PurchaseOrderStatus.DRAFT, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    supplier = relationship("Supplier", back_populates="purchase_orders")
    created_by = relationship("User")
    items = relationship("PurchaseOrderItem", back_populates="order", cascade="all, delete-orphan")
    receipts = relationship("PurchaseReceipt", back_populates="order")


class PurchaseOrderItem(Base):
    __tablename__ = "purchase_order_items"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("purchase_orders.id"), nullable=False, index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False)
    ordered_quantity: Mapped[float] = mapped_column(Numeric(12, 3), nullable=False)
    received_quantity: Mapped[float] = mapped_column(Numeric(12, 3), nullable=False, default=0)
    unit_cost: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    subtotal: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    order = relationship("PurchaseOrder", back_populates="items")
    product = relationship("Product")
    receipt_items = relationship("PurchaseReceiptItem", back_populates="order_item")


class PurchaseReceipt(Base):
    __tablename__ = "purchase_receipts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"), nullable=False, index=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("purchase_orders.id"), nullable=False, index=True)
    received_by_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    received_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    order = relationship("PurchaseOrder", back_populates="receipts")
    received_by = relationship("User")
    items = relationship("PurchaseReceiptItem", back_populates="receipt", cascade="all, delete-orphan")


class PurchaseReceiptItem(Base):
    __tablename__ = "purchase_receipt_items"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    receipt_id: Mapped[int] = mapped_column(ForeignKey("purchase_receipts.id"), nullable=False, index=True)
    order_item_id: Mapped[int] = mapped_column(ForeignKey("purchase_order_items.id"), nullable=False)
    quantity: Mapped[float] = mapped_column(Numeric(12, 3), nullable=False)
    unit_cost: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    receipt = relationship("PurchaseReceipt", back_populates="items")
    order_item = relationship("PurchaseOrderItem", back_populates="receipt_items")


class SupplierPriceHistory(Base):
    __tablename__ = "supplier_price_history"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"), nullable=False, index=True)
    supplier_id: Mapped[int] = mapped_column(ForeignKey("suppliers.id"), nullable=False, index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), nullable=False, index=True)
    receipt_id: Mapped[int] = mapped_column(ForeignKey("purchase_receipts.id"), nullable=False)
    unit_cost: Mapped[float] = mapped_column(Numeric(12, 2), nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    supplier = relationship("Supplier")
    product = relationship("Product")
    receipt = relationship("PurchaseReceipt")
