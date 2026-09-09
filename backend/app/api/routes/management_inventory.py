from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.auth.dependencies import require_permission
from app.core.permissions import PermissionCode
from app.database.session import get_db
from app.models.management_inventory import InventoryCount, InventoryCountStatus, InventoryLoss, ProductLot
from app.models.user import User
from app.schemas.management_inventory import InventoryCountComplete, InventoryCountCreate, InventoryCountItemResponse, InventoryCountResponse, LossCreate, LossResponse, LotCreate, LotResponse
from app.services.audit import log_audit
from app.services.inventory import StockValidationError
from app.services.management_inventory import ManagementInventoryError, complete_inventory_count, create_inventory_count, create_lot, expiry_state, register_loss

router = APIRouter()


def serialize_lot(lot: ProductLot) -> LotResponse:
    state, days = expiry_state(lot.expiration_date)
    return LotResponse(id=lot.id, product_id=lot.product_id, product_name=lot.product.name, supplier_name=lot.supplier.name if lot.supplier else None, lot_code=lot.lot_code, initial_quantity=float(lot.initial_quantity), current_quantity=float(lot.current_quantity), unit_cost=float(lot.unit_cost), entry_date=lot.entry_date, expiration_date=lot.expiration_date, expiry_state=state, days_remaining=days, status=lot.status, created_at=lot.created_at)


def serialize_inventory(inventory: InventoryCount) -> InventoryCountResponse:
    differences = [float(item.difference or 0) for item in inventory.items]
    return InventoryCountResponse(id=inventory.id, number=f"#{inventory.id:06d}", responsible_name=inventory.created_by.name, category_name=inventory.category.name if inventory.category else None, notes=inventory.notes, status=inventory.status, created_at=inventory.created_at, completed_at=inventory.completed_at, positive_differences=sum(value for value in differences if value > 0), negative_differences=sum(value for value in differences if value < 0), items=[InventoryCountItemResponse(id=item.id, product_id=item.product_id, product_name=item.product.name, system_quantity=float(item.system_quantity), counted_quantity=float(item.counted_quantity) if item.counted_quantity is not None else None, difference=float(item.difference) if item.difference is not None else None) for item in inventory.items])


@router.get("/lots", response_model=list[LotResponse])
def list_lots(expiry: str | None = None, product_id: int | None = None, db: Session = Depends(get_db), user: User = Depends(require_permission(PermissionCode.LOTS_VIEW))):
    query = db.query(ProductLot).filter(ProductLot.account_id == user.account_id)
    if product_id: query = query.filter(ProductLot.product_id == product_id)
    lots = query.order_by(ProductLot.expiration_date.asc()).all()
    return [serialize_lot(lot) for lot in lots if not expiry or expiry_state(lot.expiration_date)[0] == expiry]


@router.get("/expiry-alerts", response_model=list[LotResponse])
def expiry_alerts(days: int = Query(default=30, ge=0, le=365), db: Session = Depends(get_db), user: User = Depends(require_permission(PermissionCode.LOTS_VIEW))):
    lots = db.query(ProductLot).filter(ProductLot.account_id == user.account_id, ProductLot.current_quantity > 0, ProductLot.expiration_date.is_not(None)).order_by(ProductLot.expiration_date).all()
    return [serialize_lot(lot) for lot in lots if (expiry_state(lot.expiration_date)[1] or 0) <= days]


@router.post("/lots", response_model=LotResponse, status_code=status.HTTP_201_CREATED)
def add_lot(payload: LotCreate, db: Session = Depends(get_db), user: User = Depends(require_permission(PermissionCode.LOTS_MANAGE))):
    try:
        lot = create_lot(db, payload, user); log_audit(db, user, action="CREATE", entity_type="LOT", entity_id=lot.id, description=f"Registrou lote de {lot.product.name}."); db.commit(); db.refresh(lot); return serialize_lot(lot)
    except (ManagementInventoryError, StockValidationError) as exc:
        db.rollback(); raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/losses", response_model=list[LossResponse])
def list_losses(db: Session = Depends(get_db), user: User = Depends(require_permission(PermissionCode.LOTS_VIEW))):
    losses = db.query(InventoryLoss).filter(InventoryLoss.account_id == user.account_id).order_by(InventoryLoss.created_at.desc()).all()
    return [LossResponse(id=item.id, product_name=item.product.name, lot_code=item.lot.lot_code if item.lot else None, quantity=float(item.quantity), reason=item.reason, notes=item.notes, user_name=item.user.name, created_at=item.created_at) for item in losses]


@router.post("/losses", response_model=LossResponse, status_code=status.HTTP_201_CREATED)
def add_loss(payload: LossCreate, db: Session = Depends(get_db), user: User = Depends(require_permission(PermissionCode.LOTS_MANAGE))):
    try:
        item = register_loss(db, payload, user); log_audit(db, user, action="LOSS", entity_type="INVENTORY_LOSS", entity_id=item.id, description=f"Registrou perda de {float(item.quantity):g} de {item.product.name}."); db.commit(); db.refresh(item); return LossResponse(id=item.id, product_name=item.product.name, lot_code=item.lot.lot_code if item.lot else None, quantity=float(item.quantity), reason=item.reason, notes=item.notes, user_name=item.user.name, created_at=item.created_at)
    except (ManagementInventoryError, StockValidationError) as exc:
        db.rollback(); raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/counts", response_model=list[InventoryCountResponse])
def list_counts(db: Session = Depends(get_db), user: User = Depends(require_permission(PermissionCode.INVENTORY_COUNT))):
    return [serialize_inventory(item) for item in db.query(InventoryCount).filter(InventoryCount.account_id == user.account_id).order_by(InventoryCount.created_at.desc()).all()]


@router.post("/counts", response_model=InventoryCountResponse, status_code=status.HTTP_201_CREATED)
def add_count(payload: InventoryCountCreate, db: Session = Depends(get_db), user: User = Depends(require_permission(PermissionCode.INVENTORY_COUNT))):
    try:
        inventory = create_inventory_count(db, payload, user); db.commit(); db.refresh(inventory); return serialize_inventory(inventory)
    except ManagementInventoryError as exc:
        db.rollback(); raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/counts/{inventory_id}/complete", response_model=InventoryCountResponse)
def complete_count(inventory_id: int, payload: InventoryCountComplete, db: Session = Depends(get_db), user: User = Depends(require_permission(PermissionCode.INVENTORY_COUNT))):
    inventory = db.query(InventoryCount).filter(InventoryCount.id == inventory_id, InventoryCount.account_id == user.account_id).first()
    if not inventory: raise HTTPException(status_code=404, detail="Inventário não encontrado.")
    try:
        complete_inventory_count(db, inventory, payload, user); log_audit(db, user, action="COMPLETE", entity_type="INVENTORY_COUNT", entity_id=inventory.id, description=f"Concluiu o inventário #{inventory.id}."); db.commit(); db.refresh(inventory); return serialize_inventory(inventory)
    except (ManagementInventoryError, StockValidationError) as exc:
        db.rollback(); raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/counts/{inventory_id}/cancel", response_model=InventoryCountResponse)
def cancel_count(inventory_id: int, db: Session = Depends(get_db), user: User = Depends(require_permission(PermissionCode.INVENTORY_COUNT))):
    inventory = db.query(InventoryCount).filter(InventoryCount.id == inventory_id, InventoryCount.account_id == user.account_id).first()
    if not inventory: raise HTTPException(status_code=404, detail="Inventário não encontrado.")
    if inventory.status != InventoryCountStatus.IN_PROGRESS: raise HTTPException(status_code=400, detail="Somente inventário em andamento pode ser cancelado.")
    inventory.status = InventoryCountStatus.CANCELLED; log_audit(db, user, action="CANCEL", entity_type="INVENTORY_COUNT", entity_id=inventory.id, description=f"Cancelou o inventário #{inventory.id}."); db.commit(); db.refresh(inventory); return serialize_inventory(inventory)
