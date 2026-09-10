from datetime import date, datetime
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.datetime import local_today
from app.models.management_inventory import InventoryCount, InventoryCountItem, InventoryCountStatus, InventoryLoss, LotStatus, ProductLot
from app.models.product import Product
from app.models.stock_movement import StockMovementType
from app.models.supplier import Supplier
from app.models.user import User
from app.schemas.management_inventory import InventoryCountComplete, InventoryCountCreate, LossCreate, LotCreate
from app.services.inventory import StockValidationError, apply_stock_movement


class ManagementInventoryError(Exception):
    pass


def expiry_state(expiration_date: date | None) -> tuple[str, int | None]:
    if expiration_date is None:
        return "SEM_VALIDADE", None
    days = (expiration_date - local_today()).days
    if days < 0: return "VENCIDO", days
    if days == 0: return "VENCE_HOJE", days
    if days <= 3: return "ATE_3_DIAS", days
    if days <= 7: return "ATE_7_DIAS", days
    if days <= 30: return "ATE_30_DIAS", days
    return "NORMAL", days


def get_product(db: Session, account_id: int, product_id: int) -> Product:
    product = db.query(Product).filter(Product.id == product_id, Product.account_id == account_id, Product.active.is_(True)).first()
    if not product:
        raise ManagementInventoryError("Produto não encontrado.")
    return product


def create_lot(db: Session, payload: LotCreate, user: User) -> ProductLot:
    product = get_product(db, user.account_id, payload.product_id)
    if payload.supplier_id and not db.query(Supplier).filter(Supplier.id == payload.supplier_id, Supplier.account_id == user.account_id).first():
        raise ManagementInventoryError("Fornecedor não encontrado.")
    lot = ProductLot(account_id=user.account_id, product_id=product.id, supplier_id=payload.supplier_id, lot_code=payload.lot_code, initial_quantity=payload.quantity, current_quantity=payload.quantity, unit_cost=payload.unit_cost, entry_date=payload.entry_date, expiration_date=payload.expiration_date)
    db.add(lot)
    db.flush()
    if payload.add_to_stock:
        apply_stock_movement(db, product=product, user=user, movement_type=StockMovementType.ENTRADA, quantity=payload.quantity, reason=f"Entrada do lote {payload.lot_code or f'#{lot.id}'}", reference_type="lot", reference_id=lot.id)
    return lot


def register_loss(db: Session, payload: LossCreate, user: User) -> InventoryLoss:
    product = get_product(db, user.account_id, payload.product_id)
    lot = None
    if payload.lot_id:
        lot = db.query(ProductLot).filter(ProductLot.id == payload.lot_id, ProductLot.account_id == user.account_id).first()
        if not lot or lot.product_id != product.id:
            raise ManagementInventoryError("Lote inválido para este produto.")
        if Decimal(str(lot.current_quantity)) < Decimal(str(payload.quantity)):
            raise ManagementInventoryError("A quantidade da perda supera o saldo do lote.")
        lot.current_quantity = Decimal(str(lot.current_quantity)) - Decimal(str(payload.quantity))
        if lot.current_quantity <= 0:
            lot.status = LotStatus.DEPLETED
    loss = InventoryLoss(account_id=user.account_id, product_id=product.id, lot_id=lot.id if lot else None, user_id=user.id, quantity=payload.quantity, unit_cost=lot.unit_cost if lot else product.cost_price, reason=payload.reason, notes=payload.notes)
    db.add(loss)
    db.flush()
    apply_stock_movement(db, product=product, user=user, movement_type=StockMovementType.PERDA, quantity=payload.quantity, reason=f"{payload.reason.value}: {payload.notes or 'sem observação'}", reference_type="inventory_loss", reference_id=loss.id)
    return loss


def create_inventory_count(db: Session, payload: InventoryCountCreate, user: User) -> InventoryCount:
    query = db.query(Product).filter(Product.account_id == user.account_id, Product.active.is_(True))
    if payload.category_id:
        query = query.filter(Product.category_id == payload.category_id)
    if payload.product_ids:
        query = query.filter(Product.id.in_(payload.product_ids))
    products = query.order_by(Product.name).all()
    if not products:
        raise ManagementInventoryError("Nenhum produto foi selecionado para o inventário.")
    inventory = InventoryCount(account_id=user.account_id, created_by_id=user.id, category_id=payload.category_id, notes=payload.notes)
    db.add(inventory)
    for product in products:
        inventory.items.append(InventoryCountItem(product_id=product.id, system_quantity=product.stock_quantity))
    db.flush()
    return inventory


def complete_inventory_count(db: Session, inventory: InventoryCount, payload: InventoryCountComplete, user: User) -> InventoryCount:
    if inventory.status != InventoryCountStatus.IN_PROGRESS:
        raise ManagementInventoryError("Este inventário não está em andamento.")
    submitted = {item.product_id: item.counted_quantity for item in payload.items}
    if set(submitted) != {item.product_id for item in inventory.items}:
        raise ManagementInventoryError("Informe a contagem de todos os produtos do inventário.")
    for item in inventory.items:
        counted = submitted[item.product_id]
        item.counted_quantity = counted
        item.difference = Decimal(str(counted)) - Decimal(str(item.system_quantity))
        if item.difference != 0:
            apply_stock_movement(db, product=item.product, user=user, movement_type=StockMovementType.INVENTARIO, quantity=abs(float(item.difference)), target_stock=counted, reason=f"Inventário #{inventory.id}", reference_type="inventory_count", reference_id=inventory.id)
    inventory.status = InventoryCountStatus.COMPLETED
    inventory.completed_at = datetime.utcnow()
    return inventory
