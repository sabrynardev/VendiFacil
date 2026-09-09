from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.auth.dependencies import require_any_permission, require_permission
from app.core.permissions import PermissionCode
from app.database.session import get_db
from app.models.sale import PaymentMethod, Sale, SaleStatus
from app.models.user import User
from app.schemas.sale import HoldSaleCreate, PaymentResponse, SaleCancel, SaleCreate, SaleItemResponse, SaleResponse
from app.services.audit import log_audit
from app.services.sales import SaleValidationError, cancel_sale, create_sale, hold_sale
from app.services.inventory import StockValidationError
from app.services.profiles import permission_codes_for_user

router = APIRouter()


def serialize_sale(sale: Sale) -> SaleResponse:
    payments = [PaymentResponse(id=p.id, method=p.method, amount=float(p.amount), amount_received=float(p.amount_received) if p.amount_received is not None else None, change_amount=float(p.change_amount)) for p in sale.payments]
    if not payments and sale.status == SaleStatus.COMPLETED and sale.payment_method in {item.value for item in PaymentMethod}:
        payments = [PaymentResponse(id=0, method=PaymentMethod(sale.payment_method), amount=float(sale.total), amount_received=float(sale.amount_received) if sale.amount_received is not None else float(sale.total), change_amount=float(sale.change_amount or 0))]
    return SaleResponse(
        id=sale.id, number=f"#{sale.id:06d}", user_id=sale.user_id, operator_name=sale.user.name,
        cash_register_id=sale.cash_register_id, customer_id=sale.customer_id, customer_name=sale.customer.name if sale.customer else None, credit_due_date=sale.credit_due_date, subtotal=float(sale.subtotal), discount=float(sale.discount),
        surcharge=float(sale.surcharge or 0), total=float(sale.total), payment_method=sale.payment_method,
        amount_received=float(sale.amount_received) if sale.amount_received is not None else None,
        change_amount=float(sale.change_amount) if sale.change_amount is not None else None,
        status=sale.status, note=sale.note, cancellation_reason=sale.cancellation_reason,
        cancelled_at=sale.cancelled_at, created_at=sale.created_at,
        items=[SaleItemResponse(id=i.id, product_id=i.product_id, product_name=i.product.name, product_unit=i.product.unit, quantity=float(i.quantity), unit_price=float(i.unit_price), discount=float(i.discount), subtotal=float(i.subtotal)) for i in sale.items],
        payments=payments,
    )


@router.get("", response_model=list[SaleResponse])
def list_sales(
    sale_status: SaleStatus | None = Query(default=None, alias="status"),
    payment_method: str | None = None,
    operator_id: int | None = None,
    date_from: datetime | None = None,
    date_to: datetime | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_any_permission(PermissionCode.SALES_VIEW, PermissionCode.CASHIER_OPERATE)),
):
    query = db.query(Sale).filter(Sale.account_id == current_user.account_id)
    if PermissionCode.SALES_VIEW.value not in permission_codes_for_user(current_user):
        query = query.filter(Sale.user_id == current_user.id)
    if sale_status: query = query.filter(Sale.status == sale_status)
    if payment_method: query = query.filter(Sale.payment_method.contains(payment_method.upper()))
    if operator_id: query = query.filter(Sale.user_id == operator_id)
    if date_from: query = query.filter(Sale.created_at >= date_from)
    if date_to: query = query.filter(Sale.created_at <= date_to)
    return [serialize_sale(sale) for sale in query.order_by(Sale.created_at.desc()).all()]


@router.get("/detail/{sale_id}", response_model=SaleResponse)
def get_sale(sale_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_any_permission(PermissionCode.SALES_VIEW, PermissionCode.CASHIER_OPERATE))):
    sale = db.query(Sale).filter(Sale.id == sale_id, Sale.account_id == current_user.account_id).first()
    if not sale: raise HTTPException(status_code=404, detail="Venda não encontrada.")
    return serialize_sale(sale)


@router.post("", response_model=SaleResponse, status_code=status.HTTP_201_CREATED)
def create_sale_endpoint(payload: SaleCreate, db: Session = Depends(get_db), current_user: User = Depends(require_permission(PermissionCode.CASHIER_OPERATE))):
    try:
        sale, authorizer = create_sale(db, payload, current_user)
        log_audit(db, current_user, action="CREATE", entity_type="SALE", entity_id=sale.id, description=f"Concluiu a venda #{sale.id} no valor de R$ {float(sale.total):.2f}.")
        if authorizer:
            log_audit(db, current_user, action="SPECIAL_DISCOUNT", entity_type="SALE", entity_id=sale.id, description=f"Desconto especial autorizado por {authorizer.name}.", changes={"authorized_by": authorizer.id})
        if sale.credit_authorized_by_id:
            log_audit(db, current_user, action="CREDIT_OVERRIDE", entity_type="SALE", entity_id=sale.id, description=f"Excesso de limite autorizado por {sale.credit_authorized_by.name}.", changes={"authorized_by": sale.credit_authorized_by_id})
        db.commit(); db.refresh(sale)
        return serialize_sale(sale)
    except SaleValidationError as exc:
        db.rollback(); raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/hold", response_model=SaleResponse, status_code=status.HTTP_201_CREATED)
def hold_sale_endpoint(payload: HoldSaleCreate, db: Session = Depends(get_db), current_user: User = Depends(require_permission(PermissionCode.CASHIER_OPERATE))):
    try:
        sale = hold_sale(db, payload, current_user); db.commit(); db.refresh(sale); return serialize_sale(sale)
    except SaleValidationError as exc:
        db.rollback(); raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/{sale_id}/complete", response_model=SaleResponse)
def complete_held_sale(sale_id: int, payload: SaleCreate, db: Session = Depends(get_db), current_user: User = Depends(require_permission(PermissionCode.CASHIER_OPERATE))):
    held = db.query(Sale).filter(Sale.id == sale_id, Sale.account_id == current_user.account_id, Sale.user_id == current_user.id).first()
    if not held: raise HTTPException(status_code=404, detail="Venda em espera não encontrada.")
    try:
        sale, authorizer = create_sale(db, payload, current_user, held)
        log_audit(db, current_user, action="COMPLETE", entity_type="SALE", entity_id=sale.id, description=f"Concluiu a venda em espera #{sale.id}.")
        if authorizer: log_audit(db, current_user, action="SPECIAL_DISCOUNT", entity_type="SALE", entity_id=sale.id, description=f"Desconto especial autorizado por {authorizer.name}.")
        if sale.credit_authorized_by_id: log_audit(db, current_user, action="CREDIT_OVERRIDE", entity_type="SALE", entity_id=sale.id, description=f"Excesso de limite autorizado por {sale.credit_authorized_by.name}.")
        db.commit(); db.refresh(sale); return serialize_sale(sale)
    except SaleValidationError as exc:
        db.rollback(); raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/{sale_id}/cancel", response_model=SaleResponse)
def cancel_sale_endpoint(sale_id: int, payload: SaleCancel, db: Session = Depends(get_db), current_user: User = Depends(require_any_permission(PermissionCode.SALES_CANCEL, PermissionCode.CASHIER_OPERATE))):
    sale = db.query(Sale).filter(Sale.id == sale_id, Sale.account_id == current_user.account_id).first()
    if not sale: raise HTTPException(status_code=404, detail="Venda não encontrada.")
    permissions = permission_codes_for_user(current_user)
    if sale.status == SaleStatus.ON_HOLD and sale.user_id != current_user.id and PermissionCode.SALES_CANCEL.value not in permissions:
        raise HTTPException(status_code=403, detail="Você só pode cancelar suas próprias vendas em espera.")
    if sale.status != SaleStatus.ON_HOLD and PermissionCode.SALES_CANCEL.value not in permissions:
        raise HTTPException(status_code=403, detail="Apenas gerente ou administrador pode cancelar uma venda concluída.")
    try:
        cancel_sale(db, sale, current_user, payload.reason)
        log_audit(db, current_user, action="CANCEL", entity_type="SALE", entity_id=sale.id, description=f"Cancelou a venda #{sale.id}.", changes={"reason": payload.reason})
        db.commit(); db.refresh(sale); return serialize_sale(sale)
    except (SaleValidationError, StockValidationError) as exc:
        db.rollback(); raise HTTPException(status_code=400, detail=str(exc)) from exc
