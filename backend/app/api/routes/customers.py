from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.auth.dependencies import require_permission
from app.core.datetime import local_today, utc_to_local
from app.core.permissions import PermissionCode
from app.database.session import get_db
from app.models.customer import Customer, DebtStatus
from app.models.user import User
from app.schemas.customer import CustomerCreate, CustomerDebtResponse, CustomerPaymentCreate, CustomerPaymentResponse, CustomerResponse, CustomerSaleResponse, CustomerUpdate
from app.services.audit import log_audit
from app.services.customers import CustomerValidationError, customer_balance, customer_sales_summary, debt_is_overdue, register_customer_payment

router = APIRouter()


def serialize_customer(db: Session, customer: Customer, details: bool = False) -> CustomerResponse:
    balance = customer_balance(customer)
    total, average, last_purchase, sales = customer_sales_summary(db, customer)
    debts = [CustomerDebtResponse(id=debt.id, sale_id=debt.sale_id, sale_number=f"#{debt.sale_id:06d}", amount=float(debt.amount), balance=float(debt.balance), due_date=debt.due_date, status=debt.status, is_overdue=debt_is_overdue(debt), days_open=(local_today()-utc_to_local(debt.created_at).date()).days, created_at=debt.created_at) for debt in customer.debts] if details else []
    payments = [CustomerPaymentResponse(id=item.id, amount=float(item.amount), method=item.method, responsible_name=item.received_by.name, balance_before=float(item.balance_before), balance_after=float(item.balance_after), notes=item.notes, created_at=item.created_at) for item in sorted(customer.payments, key=lambda entry: entry.created_at, reverse=True)] if details else []
    overdue = sum(float(debt.balance) for debt in customer.debts if debt_is_overdue(debt))
    sale_history = [CustomerSaleResponse(id=sale.id, number=f"#{sale.id:06d}", total=float(sale.total), payment_method=sale.payment_method, status=sale.status.value, created_at=sale.created_at) for sale in sales] if details else []
    return CustomerResponse(id=customer.id, name=customer.name, phone=customer.phone, whatsapp=customer.whatsapp, cpf=customer.cpf, address=customer.address, notes=customer.notes, credit_limit=float(customer.credit_limit) if customer.credit_limit is not None else None, credit_blocked=customer.credit_blocked, active=customer.active, balance=float(balance), available_credit=float(customer.credit_limit-balance) if customer.credit_limit is not None else None, total_purchased=float(total), ticket_average=average, last_purchase_at=last_purchase, overdue_balance=overdue, created_at=customer.created_at, updated_at=customer.updated_at, debts=debts, payments=payments, sales=sale_history)


@router.get("", response_model=list[CustomerResponse])
def list_customers(search: str | None = None, overdue: bool = False, db: Session = Depends(get_db), user: User = Depends(require_permission(PermissionCode.CUSTOMERS_VIEW))):
    query = db.query(Customer).filter(Customer.account_id == user.account_id, Customer.active.is_(True))
    if search:
        term = f"%{search.strip()}%"; query = query.filter(or_(Customer.name.ilike(term), Customer.phone.ilike(term), Customer.cpf.ilike(term)))
    customers = query.order_by(Customer.name).all()
    results = [serialize_customer(db, customer) for customer in customers]
    return [item for item in results if not overdue or item.overdue_balance > 0]


@router.get("/{customer_id}", response_model=CustomerResponse)
def get_customer(customer_id: int, db: Session = Depends(get_db), user: User = Depends(require_permission(PermissionCode.CUSTOMERS_VIEW))):
    customer = db.query(Customer).filter(Customer.id == customer_id, Customer.account_id == user.account_id).first()
    if not customer: raise HTTPException(status_code=404, detail="Cliente não encontrado.")
    return serialize_customer(db, customer, True)


@router.post("", response_model=CustomerResponse, status_code=status.HTTP_201_CREATED)
def create_customer(payload: CustomerCreate, db: Session = Depends(get_db), user: User = Depends(require_permission(PermissionCode.CUSTOMERS_MANAGE))):
    customer = Customer(account_id=user.account_id, **payload.model_dump()); db.add(customer); db.flush(); log_audit(db, user, action="CREATE", entity_type="CUSTOMER", entity_id=customer.id, description=f"Cadastrou o cliente {customer.name}."); db.commit(); db.refresh(customer); return serialize_customer(db, customer)


@router.put("/{customer_id}", response_model=CustomerResponse)
def update_customer(customer_id: int, payload: CustomerUpdate, db: Session = Depends(get_db), user: User = Depends(require_permission(PermissionCode.CUSTOMERS_MANAGE))):
    customer = db.query(Customer).filter(Customer.id == customer_id, Customer.account_id == user.account_id).first()
    if not customer: raise HTTPException(status_code=404, detail="Cliente não encontrado.")
    before = {"credit_limit": float(customer.credit_limit) if customer.credit_limit is not None else None, "credit_blocked": customer.credit_blocked}
    for field, value in payload.model_dump().items(): setattr(customer, field, value)
    after = {"credit_limit": float(customer.credit_limit) if customer.credit_limit is not None else None, "credit_blocked": customer.credit_blocked}
    log_audit(db, user, action="UPDATE", entity_type="CUSTOMER", entity_id=customer.id, description=f"Atualizou o cliente {customer.name}.", changes={"before": before, "after": after}); db.commit(); db.refresh(customer); return serialize_customer(db, customer)


@router.post("/{customer_id}/payments", response_model=CustomerPaymentResponse, status_code=status.HTTP_201_CREATED)
def add_payment(customer_id: int, payload: CustomerPaymentCreate, db: Session = Depends(get_db), user: User = Depends(require_permission(PermissionCode.CREDIT_RECEIVE))):
    customer = db.query(Customer).filter(Customer.id == customer_id, Customer.account_id == user.account_id).first()
    if not customer: raise HTTPException(status_code=404, detail="Cliente não encontrado.")
    try:
        payment = register_customer_payment(db, customer, payload, user); log_audit(db, user, action="CREDIT_PAYMENT", entity_type="CUSTOMER", entity_id=customer.id, description=f"Recebeu R$ {float(payment.amount):.2f} de {customer.name}."); db.commit(); db.refresh(payment); return CustomerPaymentResponse(id=payment.id, amount=float(payment.amount), method=payment.method, responsible_name=payment.received_by.name, balance_before=float(payment.balance_before), balance_after=float(payment.balance_after), notes=payment.notes, created_at=payment.created_at)
    except CustomerValidationError as exc:
        db.rollback(); raise HTTPException(status_code=400, detail=str(exc)) from exc
