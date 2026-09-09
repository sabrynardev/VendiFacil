from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.auth.dependencies import require_permission
from app.core.permissions import PermissionCode
from app.database.session import get_db
from app.models.purchase import ProductSupplier, PurchaseOrder, PurchaseOrderStatus, SupplierPriceHistory
from app.models.supplier import Supplier
from app.models.user import User
from app.schemas.purchase import PriceHistoryResponse, ProductSupplierCreate, ProductSupplierResponse, PurchaseItemResponse, PurchaseOrderCreate, PurchaseOrderResponse, PurchaseReceiptCreate
from app.services.audit import log_audit
from app.services.inventory import StockValidationError
from app.services.purchases import PurchaseValidationError, create_order, get_supplier, link_supplier, receive_order

router = APIRouter()


def serialize_link(link: ProductSupplier) -> ProductSupplierResponse:
    return ProductSupplierResponse(id=link.id, product_id=link.product_id, product_name=link.product.name, supplier_id=link.supplier_id, supplier_name=link.supplier.name, supplier_code=link.supplier_code, last_price=float(link.last_price) if link.last_price is not None else None, last_purchase_at=link.last_purchase_at, preferred=link.preferred, lead_time_days=link.lead_time_days)


def serialize_order(order: PurchaseOrder) -> PurchaseOrderResponse:
    return PurchaseOrderResponse(id=order.id, number=f"#{order.id:06d}", supplier_id=order.supplier_id, supplier_name=order.supplier.name, created_by_name=order.created_by.name, order_date=order.order_date, expected_date=order.expected_date, notes=order.notes, subtotal=float(order.subtotal), discount=float(order.discount), total=float(order.total), status=order.status, created_at=order.created_at, updated_at=order.updated_at, items=[PurchaseItemResponse(id=item.id, product_id=item.product_id, product_name=item.product.name, product_unit=item.product.unit, ordered_quantity=float(item.ordered_quantity), received_quantity=float(item.received_quantity), pending_quantity=float(item.ordered_quantity-item.received_quantity), unit_cost=float(item.unit_cost), subtotal=float(item.subtotal), notes=item.notes) for item in order.items])


@router.get("", response_model=list[PurchaseOrderResponse])
def list_orders(order_status: PurchaseOrderStatus | None = Query(default=None, alias="status"), supplier_id: int | None = None, db: Session = Depends(get_db), user: User = Depends(require_permission(PermissionCode.PURCHASES_VIEW))):
    query = db.query(PurchaseOrder).filter(PurchaseOrder.account_id == user.account_id)
    if order_status: query = query.filter(PurchaseOrder.status == order_status)
    if supplier_id: query = query.filter(PurchaseOrder.supplier_id == supplier_id)
    return [serialize_order(order) for order in query.order_by(PurchaseOrder.created_at.desc()).all()]


@router.get("/{order_id}", response_model=PurchaseOrderResponse)
def get_order(order_id: int, db: Session = Depends(get_db), user: User = Depends(require_permission(PermissionCode.PURCHASES_VIEW))):
    order = db.query(PurchaseOrder).filter(PurchaseOrder.id == order_id, PurchaseOrder.account_id == user.account_id).first()
    if not order: raise HTTPException(status_code=404, detail="Pedido não encontrado.")
    return serialize_order(order)


@router.post("", response_model=PurchaseOrderResponse, status_code=status.HTTP_201_CREATED)
def create(payload: PurchaseOrderCreate, db: Session = Depends(get_db), user: User = Depends(require_permission(PermissionCode.PURCHASES_MANAGE))):
    try:
        order = create_order(db, payload, user)
        log_audit(db, user, action="CREATE", entity_type="PURCHASE_ORDER", entity_id=order.id, description=f"Criou o pedido #{order.id} para {order.supplier.name}.")
        db.commit(); db.refresh(order); return serialize_order(order)
    except PurchaseValidationError as exc:
        db.rollback(); raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/{order_id}/receive", response_model=PurchaseOrderResponse)
def receive(order_id: int, payload: PurchaseReceiptCreate, db: Session = Depends(get_db), user: User = Depends(require_permission(PermissionCode.PURCHASES_MANAGE))):
    order = db.query(PurchaseOrder).filter(PurchaseOrder.id == order_id, PurchaseOrder.account_id == user.account_id).first()
    if not order: raise HTTPException(status_code=404, detail="Pedido não encontrado.")
    try:
        receipt = receive_order(db, order, payload, user)
        log_audit(db, user, action="RECEIVE", entity_type="PURCHASE_ORDER", entity_id=order.id, description=f"Registrou o recebimento #{receipt.id} do pedido #{order.id}.")
        db.commit(); db.refresh(order); return serialize_order(order)
    except (PurchaseValidationError, StockValidationError) as exc:
        db.rollback(); raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/{order_id}/cancel", response_model=PurchaseOrderResponse)
def cancel(order_id: int, db: Session = Depends(get_db), user: User = Depends(require_permission(PermissionCode.PURCHASES_MANAGE))):
    order = db.query(PurchaseOrder).filter(PurchaseOrder.id == order_id, PurchaseOrder.account_id == user.account_id).first()
    if not order: raise HTTPException(status_code=404, detail="Pedido não encontrado.")
    if order.status in {PurchaseOrderStatus.RECEIVED, PurchaseOrderStatus.PARTIALLY_RECEIVED}: raise HTTPException(status_code=400, detail="Pedido com recebimento não pode ser cancelado.")
    order.status = PurchaseOrderStatus.CANCELLED
    log_audit(db, user, action="CANCEL", entity_type="PURCHASE_ORDER", entity_id=order.id, description=f"Cancelou o pedido #{order.id}.")
    db.commit(); db.refresh(order); return serialize_order(order)


@router.post("/suppliers/{supplier_id}/products", response_model=ProductSupplierResponse)
def add_supplier_product(supplier_id: int, payload: ProductSupplierCreate, db: Session = Depends(get_db), user: User = Depends(require_permission(PermissionCode.SUPPLIERS_MANAGE))):
    try:
        supplier = get_supplier(db, user.account_id, supplier_id)
        link = link_supplier(db, supplier, payload)
        log_audit(db, user, action="LINK_PRODUCT", entity_type="SUPPLIER", entity_id=supplier.id, description=f"Vinculou {link.product.name} a {supplier.name}.")
        db.commit(); db.refresh(link); return serialize_link(link)
    except PurchaseValidationError as exc:
        db.rollback(); raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/suppliers/{supplier_id}/products", response_model=list[ProductSupplierResponse])
def supplier_products(supplier_id: int, db: Session = Depends(get_db), user: User = Depends(require_permission(PermissionCode.SUPPLIERS_VIEW))):
    get_supplier(db, user.account_id, supplier_id)
    return [serialize_link(link) for link in db.query(ProductSupplier).filter(ProductSupplier.account_id == user.account_id, ProductSupplier.supplier_id == supplier_id).all()]


@router.get("/history/prices", response_model=list[PriceHistoryResponse])
def price_history(product_id: int | None = None, supplier_id: int | None = None, db: Session = Depends(get_db), user: User = Depends(require_permission(PermissionCode.PURCHASES_VIEW))):
    query = db.query(SupplierPriceHistory).filter(SupplierPriceHistory.account_id == user.account_id)
    if product_id: query = query.filter(SupplierPriceHistory.product_id == product_id)
    if supplier_id: query = query.filter(SupplierPriceHistory.supplier_id == supplier_id)
    histories = query.order_by(SupplierPriceHistory.product_id, SupplierPriceHistory.supplier_id, SupplierPriceHistory.recorded_at).all()
    previous = {}
    responses = []
    for item in histories:
        key = (item.product_id, item.supplier_id)
        old = previous.get(key)
        current = float(item.unit_cost)
        variation = round((current - old) / old * 100, 2) if old else None
        responses.append(PriceHistoryResponse(id=item.id, supplier_id=item.supplier_id, supplier_name=item.supplier.name, product_id=item.product_id, product_name=item.product.name, unit_cost=current, previous_cost=old, variation_percent=variation, recorded_at=item.recorded_at))
        previous[key] = current
    return list(reversed(responses))
