from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.auth.dependencies import require_any_permission, require_permission
from app.core.permissions import PermissionCode
from app.database.session import get_db
from app.models.cash_register import CashMovementType, CashRegister
from app.models.user import User
from app.schemas.cash_register import CashMovementCreate, CashMovementResponse, CashRegisterClose, CashRegisterOpen, CashRegisterResponse, CashSummary
from app.services.audit import log_audit
from app.services.cash_registers import CashRegisterValidationError, add_cash_movement, close_register, current_register, open_register, register_summary
from app.services.profiles import permission_codes_for_user

router = APIRouter()


def serialize_register(register: CashRegister, details: bool = False) -> CashRegisterResponse:
    return CashRegisterResponse(id=register.id, operator_name=register.opened_by.name, closed_by_name=register.closed_by.name if register.closed_by else None, opened_at=register.opened_at, closed_at=register.closed_at, opening_balance=float(register.opening_balance), expected_balance=float(register.expected_balance) if register.expected_balance is not None else None, counted_balance=float(register.counted_balance) if register.counted_balance is not None else None, difference=float(register.difference) if register.difference is not None else None, status=register.status, closing_note=register.closing_note, summary=CashSummary(**register_summary(register)), movements=[CashMovementResponse(id=m.id, type=m.type, amount=float(m.amount), payment_method=m.payment_method, reason=m.reason, user_name=m.user.name, reference_type=m.reference_type, reference_id=m.reference_id, created_at=m.created_at) for m in register.movements] if details else [])


@router.get("/current", response_model=CashRegisterResponse | None)
def get_current(db: Session = Depends(get_db), current_user: User = Depends(require_permission(PermissionCode.CASH_REGISTER_VIEW))):
    register = current_register(db, current_user)
    return serialize_register(register, True) if register else None


@router.get("", response_model=list[CashRegisterResponse])
def history(db: Session = Depends(get_db), current_user: User = Depends(require_permission(PermissionCode.CASH_REGISTER_VIEW))):
    query = db.query(CashRegister).filter(CashRegister.account_id == current_user.account_id)
    if PermissionCode.CASH_REGISTER_MANAGE.value not in permission_codes_for_user(current_user): query = query.filter(CashRegister.opened_by_id == current_user.id)
    return [serialize_register(item) for item in query.order_by(CashRegister.opened_at.desc()).all()]


@router.get("/{register_id}", response_model=CashRegisterResponse)
def details(register_id: int, db: Session = Depends(get_db), current_user: User = Depends(require_permission(PermissionCode.CASH_REGISTER_VIEW))):
    register = db.query(CashRegister).filter(CashRegister.id == register_id, CashRegister.account_id == current_user.account_id).first()
    if not register: raise HTTPException(status_code=404, detail="Caixa não encontrado.")
    return serialize_register(register, True)


@router.post("/open", response_model=CashRegisterResponse, status_code=status.HTTP_201_CREATED)
def open_endpoint(payload: CashRegisterOpen, db: Session = Depends(get_db), current_user: User = Depends(require_permission(PermissionCode.CASH_REGISTER_OPERATE))):
    try:
        register = open_register(db, current_user, payload.opening_balance)
        log_audit(db, current_user, action="OPEN", entity_type="CASH_REGISTER", entity_id=register.id, description=f"Abriu o caixa com R$ {payload.opening_balance:.2f}.")
        db.commit(); db.refresh(register); return serialize_register(register, True)
    except CashRegisterValidationError as exc: db.rollback(); raise HTTPException(status_code=400, detail=str(exc)) from exc


def movement_endpoint(kind: CashMovementType, payload: CashMovementCreate, db: Session, user: User):
    register = current_register(db, user)
    if not register: raise HTTPException(status_code=400, detail="Não há caixa aberto.")
    if kind == CashMovementType.WITHDRAWAL and payload.amount > register_summary(register)["expected_cash"]:
        raise HTTPException(status_code=400, detail="A sangria não pode superar o dinheiro disponível no caixa.")
    movement = add_cash_movement(db, register, user, kind, payload.amount, reason=payload.reason)
    log_audit(db, user, action=kind.value, entity_type="CASH_REGISTER", entity_id=register.id, description=f"Registrou {kind.value.lower()} de R$ {payload.amount:.2f}.", changes={"reason": payload.reason})
    db.commit(); db.refresh(register); return serialize_register(register, True)


@router.post("/withdrawal", response_model=CashRegisterResponse)
def withdrawal(payload: CashMovementCreate, db: Session = Depends(get_db), current_user: User = Depends(require_any_permission(PermissionCode.CASH_REGISTER_MANAGE, PermissionCode.CASH_REGISTER_OPERATE))): return movement_endpoint(CashMovementType.WITHDRAWAL, payload, db, current_user)


@router.post("/supply", response_model=CashRegisterResponse)
def supply(payload: CashMovementCreate, db: Session = Depends(get_db), current_user: User = Depends(require_any_permission(PermissionCode.CASH_REGISTER_MANAGE, PermissionCode.CASH_REGISTER_OPERATE))): return movement_endpoint(CashMovementType.SUPPLY, payload, db, current_user)


@router.post("/close", response_model=CashRegisterResponse)
def close_endpoint(payload: CashRegisterClose, db: Session = Depends(get_db), current_user: User = Depends(require_permission(PermissionCode.CASH_REGISTER_OPERATE))):
    register = current_register(db, current_user)
    if not register: raise HTTPException(status_code=400, detail="Não há caixa aberto.")
    close_register(db, register, current_user, payload.counted_balance, payload.note)
    log_audit(db, current_user, action="CLOSE", entity_type="CASH_REGISTER", entity_id=register.id, description=f"Fechou o caixa com diferença de R$ {float(register.difference):.2f}.")
    db.commit(); db.refresh(register); return serialize_register(register, True)
