from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.auth.dependencies import require_any_permission, require_permission
from app.core.permissions import PermissionCode
from app.database.session import get_db
from app.models.customer import CustomerDebt, DebtStatus
from app.models.financial import FinancialCategory, FinancialCategoryType, FinancialReceivable, FinancialStatus, ManualRevenue, Payable, RecurringExpense
from app.models.user import User
from app.schemas.financial import CashFlowEntry, FinancialCategoryCreate, FinancialCategoryResponse, FinancialPaymentCreate, FinancialPaymentResponse, FinancialSummaryResponse, ManualRevenueCreate, ManualRevenueResponse, PayableCreate, PayableResponse, ProjectionResponse, ReceivableCreate, ReceivableResponse, ReconciliationIssue, RecurringExpenseCreate, RecurringExpenseResponse
from app.services.audit import log_audit
from app.services.financial import FinancialValidationError, cash_flow, create_manual_revenue, create_payable, create_receivable, create_recurring_expense, financial_summary, generate_recurring_payables, payable_status, projections, receivable_status, reconciliation_issues, register_payable_payment, register_receivable_receipt

router = APIRouter()


def serialize_payment(payment) -> FinancialPaymentResponse:
    return FinancialPaymentResponse(id=payment.id, amount=float(payment.amount), method=payment.method, user_name=payment.user.name, occurred_at=payment.payment_date, notes=payment.notes)


def serialize_payable(payable: Payable) -> PayableResponse:
    balance = max(float(payable.original_amount) - float(payable.paid_amount), 0)
    return PayableResponse(
        id=payable.id,
        description=payable.description,
        category_id=payable.category_id,
        category_name=payable.category.name,
        supplier_id=payable.supplier_id,
        supplier_name=payable.supplier.name if payable.supplier else None,
        purchase_order_id=payable.purchase_order_id,
        original_amount=float(payable.original_amount),
        paid_amount=float(payable.paid_amount),
        balance=balance,
        due_date=payable.due_date,
        paid_at=payable.paid_at,
        status=payable_status(payable),
        is_overdue=payable.status != FinancialStatus.CANCELLED and balance > 0 and payable.due_date < date.today(),
        payment_method=payable.payment_method,
        notes=payable.notes,
        origin=payable.origin.value,
        affects_result=payable.affects_result,
        created_at=payable.created_at,
        payments=[serialize_payment(item) for item in sorted(payable.payments, key=lambda entry: entry.payment_date, reverse=True)],
    )


def serialize_revenue(item: ManualRevenue) -> ManualRevenueResponse:
    return ManualRevenueResponse(id=item.id, description=item.description, category_name=item.category.name, amount=float(item.amount), received_at=item.received_at, competence_date=item.competence_date, payment_method=item.payment_method, reference=item.reference, notes=item.notes, cancelled=item.cancelled_at is not None, created_by_name=item.created_by.name)


def serialize_receivable(item: FinancialReceivable) -> ReceivableResponse:
    balance = max(float(item.original_amount) - float(item.received_amount), 0)
    return ReceivableResponse(id=f"manual-{item.id}", source_id=item.id, source="MANUAL", description=item.description, customer_id=item.customer_id, customer_name=item.customer.name if item.customer else None, original_amount=float(item.original_amount), received_amount=float(item.received_amount), balance=balance, due_date=item.due_date, status=receivable_status(item), is_overdue=item.status != FinancialStatus.CANCELLED and balance > 0 and item.due_date < date.today(), created_at=item.created_at)


@router.get("/categories", response_model=list[FinancialCategoryResponse])
def list_categories(category_type: FinancialCategoryType | None = Query(default=None, alias="type"), db: Session = Depends(get_db), user: User = Depends(require_permission(PermissionCode.FINANCIAL_VIEW))):
    query = db.query(FinancialCategory).filter(FinancialCategory.account_id == user.account_id, FinancialCategory.active.is_(True))
    if category_type:
        query = query.filter(FinancialCategory.type == category_type)
    return query.order_by(FinancialCategory.type, FinancialCategory.name).all()


@router.post("/categories", response_model=FinancialCategoryResponse, status_code=status.HTTP_201_CREATED)
def add_category(payload: FinancialCategoryCreate, db: Session = Depends(get_db), user: User = Depends(require_permission(PermissionCode.FINANCIAL_EXPENSE_EDIT))):
    exists = db.query(FinancialCategory).filter(FinancialCategory.account_id == user.account_id, FinancialCategory.type == payload.type, FinancialCategory.name == payload.name.strip()).first()
    if exists:
        raise HTTPException(status_code=409, detail="Já existe uma categoria financeira com esse nome.")
    category = FinancialCategory(account_id=user.account_id, name=payload.name.strip(), type=payload.type, affects_result=payload.affects_result)
    db.add(category); db.flush(); log_audit(db, user, action="CREATE", entity_type="FINANCIAL_CATEGORY", entity_id=category.id, description=f"Criou a categoria financeira {category.name}."); db.commit(); db.refresh(category); return category


@router.get("/payables", response_model=list[PayableResponse])
def list_payables(financial_status: str | None = Query(default=None, alias="status"), supplier_id: int | None = None, db: Session = Depends(get_db), user: User = Depends(require_permission(PermissionCode.FINANCIAL_PAYABLES))):
    query = db.query(Payable).filter(Payable.account_id == user.account_id)
    if supplier_id:
        query = query.filter(Payable.supplier_id == supplier_id)
    items = [serialize_payable(item) for item in query.order_by(Payable.due_date, Payable.id).all()]
    return [item for item in items if not financial_status or item.status == financial_status]


@router.post("/payables", response_model=PayableResponse, status_code=status.HTTP_201_CREATED)
def add_payable(payload: PayableCreate, db: Session = Depends(get_db), user: User = Depends(require_any_permission(PermissionCode.FINANCIAL_EXPENSE_CREATE, PermissionCode.FINANCIAL_PAYABLES))):
    try:
        payable = create_payable(db, payload, user); log_audit(db, user, action="CREATE", entity_type="PAYABLE", entity_id=payable.id, description=f"Criou a conta a pagar {payable.description} no valor de R$ {float(payable.original_amount):.2f}."); db.commit(); db.refresh(payable); return serialize_payable(payable)
    except FinancialValidationError as exc:
        db.rollback(); raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.put("/payables/{payable_id}", response_model=PayableResponse)
def update_payable(payable_id: int, payload: PayableCreate, db: Session = Depends(get_db), user: User = Depends(require_permission(PermissionCode.FINANCIAL_EXPENSE_EDIT))):
    payable = db.query(Payable).filter(Payable.id == payable_id, Payable.account_id == user.account_id).first()
    if not payable: raise HTTPException(status_code=404, detail="Conta a pagar não encontrada.")
    if float(payable.paid_amount) > 0 or payable.status == FinancialStatus.CANCELLED: raise HTTPException(status_code=400, detail="Conta paga ou cancelada não pode ser editada.")
    try:
        category = db.query(FinancialCategory).filter(FinancialCategory.id == payload.category_id, FinancialCategory.account_id == user.account_id, FinancialCategory.type == FinancialCategoryType.EXPENSE).first()
        if not category: raise FinancialValidationError("Categoria financeira inválida.")
        before = {"amount": float(payable.original_amount), "due_date": payable.due_date}
        payable.description=payload.description; payable.category_id=payload.category_id; payable.supplier_id=payload.supplier_id; payable.original_amount=payload.amount; payable.due_date=payload.due_date; payable.notes=payload.notes; payable.affects_result=category.affects_result if payload.affects_result is None else payload.affects_result
        log_audit(db, user, action="UPDATE", entity_type="PAYABLE", entity_id=payable.id, description=f"Atualizou a conta {payable.description}.", changes={"before": before, "after": {"amount": payload.amount, "due_date": payload.due_date}}); db.commit(); db.refresh(payable); return serialize_payable(payable)
    except FinancialValidationError as exc:
        db.rollback(); raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/payables/{payable_id}/payments", response_model=FinancialPaymentResponse, status_code=status.HTTP_201_CREATED)
def pay_payable(payable_id: int, payload: FinancialPaymentCreate, db: Session = Depends(get_db), user: User = Depends(require_permission(PermissionCode.FINANCIAL_PAY))):
    payable = db.query(Payable).filter(Payable.id == payable_id, Payable.account_id == user.account_id).with_for_update().first()
    if not payable: raise HTTPException(status_code=404, detail="Conta a pagar não encontrada.")
    try:
        payment = register_payable_payment(db, payable, payload, user); log_audit(db, user, action="PAY", entity_type="PAYABLE", entity_id=payable.id, description=f"Registrou pagamento de R$ {float(payment.amount):.2f} em {payable.description}."); db.commit(); db.refresh(payment); return serialize_payment(payment)
    except FinancialValidationError as exc:
        db.rollback(); raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/payables/{payable_id}/cancel", response_model=PayableResponse)
def cancel_payable(payable_id: int, reason: str = Query(min_length=3), db: Session = Depends(get_db), user: User = Depends(require_permission(PermissionCode.FINANCIAL_CANCEL))):
    payable = db.query(Payable).filter(Payable.id == payable_id, Payable.account_id == user.account_id).first()
    if not payable: raise HTTPException(status_code=404, detail="Conta a pagar não encontrada.")
    if float(payable.paid_amount) > 0: raise HTTPException(status_code=400, detail="Uma conta com pagamentos exige estorno e não pode ser cancelada diretamente.")
    payable.status=FinancialStatus.CANCELLED; log_audit(db, user, action="CANCEL", entity_type="PAYABLE", entity_id=payable.id, description=f"Cancelou {payable.description}. Motivo: {reason}"); db.commit(); db.refresh(payable); return serialize_payable(payable)


@router.get("/revenues", response_model=list[ManualRevenueResponse])
def list_revenues(db: Session = Depends(get_db), user: User = Depends(require_permission(PermissionCode.FINANCIAL_VIEW))):
    return [serialize_revenue(item) for item in db.query(ManualRevenue).filter(ManualRevenue.account_id == user.account_id).order_by(ManualRevenue.received_at.desc()).all()]


@router.post("/revenues", response_model=ManualRevenueResponse, status_code=status.HTTP_201_CREATED)
def add_revenue(payload: ManualRevenueCreate, db: Session = Depends(get_db), user: User = Depends(require_permission(PermissionCode.FINANCIAL_REVENUE_CREATE))):
    try:
        item=create_manual_revenue(db,payload,user); log_audit(db,user,action="CREATE",entity_type="MANUAL_REVENUE",entity_id=item.id,description=f"Registrou receita manual de R$ {float(item.amount):.2f}: {item.description}."); db.commit(); db.refresh(item); return serialize_revenue(item)
    except FinancialValidationError as exc:
        db.rollback(); raise HTTPException(status_code=400,detail=str(exc)) from exc


@router.post("/revenues/{revenue_id}/cancel", response_model=ManualRevenueResponse)
def cancel_revenue(revenue_id: int, reason: str = Query(min_length=3), db: Session = Depends(get_db), user: User = Depends(require_permission(PermissionCode.FINANCIAL_CANCEL))):
    item=db.query(ManualRevenue).filter(ManualRevenue.id==revenue_id,ManualRevenue.account_id==user.account_id).first()
    if not item: raise HTTPException(status_code=404,detail="Receita não encontrada.")
    if item.cancelled_at: raise HTTPException(status_code=400,detail="Receita já cancelada.")
    from datetime import datetime
    item.cancelled_at=datetime.utcnow(); log_audit(db,user,action="CANCEL",entity_type="MANUAL_REVENUE",entity_id=item.id,description=f"Cancelou a receita {item.description}. Motivo: {reason}"); db.commit(); db.refresh(item); return serialize_revenue(item)


@router.get("/receivables", response_model=list[ReceivableResponse])
def list_receivables(include_paid: bool = False, db: Session = Depends(get_db), user: User = Depends(require_permission(PermissionCode.FINANCIAL_RECEIVABLES))):
    results = [serialize_receivable(item) for item in db.query(FinancialReceivable).filter(FinancialReceivable.account_id == user.account_id).all()]
    debts = db.query(CustomerDebt).filter(CustomerDebt.account_id == user.account_id).all()
    for debt in debts:
        received=float(debt.amount)-float(debt.balance); overdue=debt.due_date is not None and debt.due_date < date.today() and float(debt.balance)>0
        results.append(ReceivableResponse(id=f"fiado-{debt.id}",source_id=debt.id,source="FIADO",description=f"Venda #{debt.sale_id:06d}",customer_id=debt.customer_id,customer_name=debt.customer.name,original_amount=float(debt.amount),received_amount=received,balance=float(debt.balance),due_date=debt.due_date,status="VENCIDA" if overdue else debt.status.value,is_overdue=overdue,created_at=debt.created_at))
    results.sort(key=lambda item: item.created_at, reverse=True)
    return results if include_paid else [item for item in results if item.balance > 0 and item.status not in {FinancialStatus.CANCELLED.value, DebtStatus.REVERSED.value}]


@router.post("/receivables", response_model=ReceivableResponse, status_code=status.HTTP_201_CREATED)
def add_receivable(payload: ReceivableCreate, db: Session = Depends(get_db), user: User = Depends(require_permission(PermissionCode.FINANCIAL_RECEIVABLES))):
    try:
        item=create_receivable(db,payload,user); log_audit(db,user,action="CREATE",entity_type="RECEIVABLE",entity_id=item.id,description=f"Criou a conta a receber {item.description}."); db.commit(); db.refresh(item); return serialize_receivable(item)
    except FinancialValidationError as exc:
        db.rollback(); raise HTTPException(status_code=400,detail=str(exc)) from exc


@router.post("/receivables/{receivable_id}/receipts", response_model=FinancialPaymentResponse, status_code=status.HTTP_201_CREATED)
def receive_receivable(receivable_id: int, payload: FinancialPaymentCreate, db: Session = Depends(get_db), user: User = Depends(require_permission(PermissionCode.FINANCIAL_RECEIVABLES))):
    item=db.query(FinancialReceivable).filter(FinancialReceivable.id==receivable_id,FinancialReceivable.account_id==user.account_id).with_for_update().first()
    if not item: raise HTTPException(status_code=404,detail="Conta a receber não encontrada.")
    try:
        receipt=register_receivable_receipt(db,item,payload,user); log_audit(db,user,action="RECEIVE",entity_type="RECEIVABLE",entity_id=item.id,description=f"Recebeu R$ {float(receipt.amount):.2f} de {item.description}."); db.commit(); db.refresh(receipt); return FinancialPaymentResponse(id=receipt.id,amount=float(receipt.amount),method=receipt.method,user_name=receipt.user.name,occurred_at=receipt.received_at,notes=receipt.notes)
    except FinancialValidationError as exc:
        db.rollback(); raise HTTPException(status_code=400,detail=str(exc)) from exc


@router.get("/recurring", response_model=list[RecurringExpenseResponse])
def list_recurring(db: Session = Depends(get_db), user: User = Depends(require_permission(PermissionCode.FINANCIAL_PAYABLES))):
    return db.query(RecurringExpense).filter(RecurringExpense.account_id==user.account_id).order_by(RecurringExpense.next_due_date).all()


@router.post("/recurring", response_model=RecurringExpenseResponse, status_code=status.HTTP_201_CREATED)
def add_recurring(payload: RecurringExpenseCreate, db: Session = Depends(get_db), user: User = Depends(require_permission(PermissionCode.FINANCIAL_EXPENSE_CREATE))):
    try:
        item=create_recurring_expense(db,payload,user); log_audit(db,user,action="CREATE",entity_type="RECURRING_EXPENSE",entity_id=item.id,description=f"Criou a despesa recorrente {item.description}."); db.commit(); db.refresh(item); return item
    except FinancialValidationError as exc:
        db.rollback(); raise HTTPException(status_code=400,detail=str(exc)) from exc


@router.post("/recurring/generate", response_model=list[PayableResponse])
def generate_recurring(through: date | None = Query(default=None), db: Session = Depends(get_db), user: User = Depends(require_permission(PermissionCode.FINANCIAL_PAYABLES))):
    target=through or date.today(); generated=generate_recurring_payables(db,user,target); log_audit(db,user,action="GENERATE",entity_type="RECURRING_EXPENSE",entity_id=None,description=f"Gerou {len(generated)} conta(s) recorrente(s) até {target}."); db.commit(); return [serialize_payable(item) for item in generated]


@router.get("/summary", response_model=FinancialSummaryResponse)
def summary(start: date, end: date, db: Session = Depends(get_db), user: User = Depends(require_permission(PermissionCode.FINANCIAL_VIEW))):
    try: return financial_summary(db,user.account_id,start,end)
    except FinancialValidationError as exc: raise HTTPException(status_code=400,detail=str(exc)) from exc


@router.get("/cash-flow", response_model=list[CashFlowEntry])
def get_cash_flow(start: date, end: date, db: Session = Depends(get_db), user: User = Depends(require_permission(PermissionCode.FINANCIAL_VIEW))):
    try: return cash_flow(db,user.account_id,start,end)
    except FinancialValidationError as exc: raise HTTPException(status_code=400,detail=str(exc)) from exc


@router.get("/projections", response_model=list[ProjectionResponse])
def get_projections(db: Session = Depends(get_db), user: User = Depends(require_permission(PermissionCode.FINANCIAL_VIEW))):
    return [projections(db,user.account_id,7),projections(db,user.account_id,30)]


@router.get("/reconciliation", response_model=list[ReconciliationIssue])
def reconciliation(db: Session = Depends(get_db), user: User = Depends(require_permission(PermissionCode.FINANCIAL_VIEW))):
    return reconciliation_issues(db,user.account_id)
