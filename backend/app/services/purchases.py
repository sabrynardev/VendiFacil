from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy.orm import Session

from app.core.products import ProductUnit
from app.models.management_inventory import ProductLot
from app.models.product import Product
from app.models.purchase import ProductSupplier, PurchaseOrder, PurchaseOrderItem, PurchaseOrderStatus, PurchaseReceipt, PurchaseReceiptItem, SupplierPriceHistory
from app.models.stock_movement import StockMovementType
from app.models.supplier import Supplier
from app.models.user import User
from app.schemas.purchase import ProductSupplierCreate, PurchaseOrderCreate, PurchaseReceiptCreate
from app.services.inventory import apply_stock_movement


class PurchaseValidationError(Exception):
    pass


def money(value) -> Decimal:
    return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def quantity(value) -> Decimal:
    return Decimal(str(value)).quantize(Decimal("0.001"), rounding=ROUND_HALF_UP)


def get_supplier(db: Session, account_id: int, supplier_id: int) -> Supplier:
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id, Supplier.account_id == account_id, Supplier.active.is_(True)).first()
    if not supplier:
        raise PurchaseValidationError("Fornecedor não encontrado.")
    return supplier


def get_product(db: Session, account_id: int, product_id: int) -> Product:
    product = db.query(Product).filter(Product.id == product_id, Product.account_id == account_id, Product.active.is_(True)).first()
    if not product:
        raise PurchaseValidationError("Produto não encontrado.")
    return product


def link_supplier(db: Session, supplier: Supplier, payload: ProductSupplierCreate) -> ProductSupplier:
    product = get_product(db, supplier.account_id, payload.product_id)
    link = db.query(ProductSupplier).filter(ProductSupplier.account_id == supplier.account_id, ProductSupplier.product_id == product.id, ProductSupplier.supplier_id == supplier.id).first()
    if not link:
        link = ProductSupplier(account_id=supplier.account_id, product_id=product.id, supplier_id=supplier.id)
        db.add(link)
    if payload.preferred:
        db.query(ProductSupplier).filter(ProductSupplier.account_id == supplier.account_id, ProductSupplier.product_id == product.id).update({ProductSupplier.preferred: False})
        product.supplier_id = supplier.id
    link.supplier_code = payload.supplier_code
    link.preferred = payload.preferred
    link.lead_time_days = payload.lead_time_days
    db.flush()
    return link


def create_order(db: Session, payload: PurchaseOrderCreate, user: User) -> PurchaseOrder:
    supplier = get_supplier(db, user.account_id, payload.supplier_id)
    order = PurchaseOrder(account_id=user.account_id, supplier_id=supplier.id, created_by_id=user.id, order_date=payload.order_date, expected_date=payload.expected_date, notes=payload.notes, discount=money(payload.discount), status=payload.status)
    db.add(order)
    subtotal = Decimal("0")
    seen = set()
    for entry in payload.items:
        if entry.product_id in seen:
            raise PurchaseValidationError("Não repita o mesmo produto no pedido.")
        seen.add(entry.product_id)
        product = get_product(db, user.account_id, entry.product_id)
        item_quantity = quantity(entry.quantity)
        if product.unit == ProductUnit.UN.value and item_quantity != item_quantity.to_integral_value():
            raise PurchaseValidationError(f"{product.name} deve usar quantidade inteira.")
        item_total = money(item_quantity * money(entry.unit_cost))
        subtotal += item_total
        order.items.append(PurchaseOrderItem(product_id=product.id, ordered_quantity=item_quantity, received_quantity=0, unit_cost=money(entry.unit_cost), subtotal=item_total, notes=entry.notes))
        existing_link = db.query(ProductSupplier).filter(ProductSupplier.account_id == user.account_id, ProductSupplier.product_id == product.id, ProductSupplier.supplier_id == supplier.id).first()
        if not existing_link:
            db.add(ProductSupplier(account_id=user.account_id, product_id=product.id, supplier_id=supplier.id, preferred=product.supplier_id == supplier.id))
    order.subtotal = money(subtotal)
    order.total = money(subtotal - money(payload.discount))
    if order.total < 0:
        raise PurchaseValidationError("O desconto não pode superar o subtotal do pedido.")
    db.flush()
    return order


def receive_order(db: Session, order: PurchaseOrder, payload: PurchaseReceiptCreate, user: User) -> PurchaseReceipt:
    if order.status in {PurchaseOrderStatus.RECEIVED, PurchaseOrderStatus.CANCELLED}:
        raise PurchaseValidationError("Este pedido não pode receber novos itens.")
    receipt = PurchaseReceipt(account_id=user.account_id, order_id=order.id, received_by_id=user.id, notes=payload.notes)
    db.add(receipt)
    db.flush()
    item_by_id = {item.id: item for item in order.items}
    seen = set()
    for entry in payload.items:
        if entry.order_item_id in seen:
            raise PurchaseValidationError("Não repita o mesmo item no recebimento.")
        seen.add(entry.order_item_id)
        item = item_by_id.get(entry.order_item_id)
        if not item:
            raise PurchaseValidationError("Item não pertence a este pedido.")
        received_now = quantity(entry.quantity)
        pending = quantity(item.ordered_quantity) - quantity(item.received_quantity)
        if received_now > pending:
            raise PurchaseValidationError(f"Recebimento de {item.product.name} supera a quantidade pendente de {float(pending):g}.")
        if item.product.unit == ProductUnit.UN.value and received_now != received_now.to_integral_value():
            raise PurchaseValidationError(f"{item.product.name} deve usar quantidade inteira.")
        cost = money(entry.unit_cost if entry.unit_cost is not None else item.unit_cost)
        item.received_quantity = quantity(item.received_quantity) + received_now
        receipt.items.append(PurchaseReceiptItem(order_item_id=item.id, quantity=received_now, unit_cost=cost))
        apply_stock_movement(db, product=item.product, user=user, movement_type=StockMovementType.COMPRA, quantity=float(received_now), reason=f"Recebimento do pedido #{order.id}", reference_type="purchase_receipt", reference_id=receipt.id)
        history = SupplierPriceHistory(account_id=user.account_id, supplier_id=order.supplier_id, product_id=item.product_id, receipt_id=receipt.id, unit_cost=cost)
        db.add(history)
        link = db.query(ProductSupplier).filter(ProductSupplier.account_id == user.account_id, ProductSupplier.product_id == item.product_id, ProductSupplier.supplier_id == order.supplier_id).first()
        if not link:
            link = ProductSupplier(account_id=user.account_id, product_id=item.product_id, supplier_id=order.supplier_id)
            db.add(link)
        link.last_price = cost
        link.last_purchase_at = receipt.received_at
        item.product.cost_price = cost
        if entry.lot_code or entry.expiration_date:
            db.add(ProductLot(account_id=user.account_id, product_id=item.product_id, supplier_id=order.supplier_id, receipt_id=receipt.id, lot_code=entry.lot_code, initial_quantity=received_now, current_quantity=received_now, unit_cost=cost, expiration_date=entry.expiration_date))
    order.status = PurchaseOrderStatus.RECEIVED if all(quantity(item.received_quantity) >= quantity(item.ordered_quantity) for item in order.items) else PurchaseOrderStatus.PARTIALLY_RECEIVED
    db.flush()
    return receipt
