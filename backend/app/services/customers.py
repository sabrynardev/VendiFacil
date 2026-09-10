from datetime import date
from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.datetime import local_today
from app.models.cash_register import CashMovementType
from app.models.customer import Customer, CustomerDebt, CustomerPayment, CustomerPaymentAllocation, DebtStatus
from app.models.sale import PaymentMethod, Sale, SaleStatus
from app.models.user import User
from app.schemas.customer import CustomerPaymentCreate
from app.services.cash_registers import add_cash_movement, current_register


class CustomerValidationError(Exception):
    pass


def money(value) -> Decimal:
    return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def customer_balance(customer: Customer) -> Decimal:
    return money(sum((money(debt.balance) for debt in customer.debts if debt.status != DebtStatus.REVERSED), Decimal("0")))


def register_customer_payment(db: Session, customer: Customer, payload: CustomerPaymentCreate, user: User) -> CustomerPayment:
    if payload.method == PaymentMethod.CREDIT_ACCOUNT:
        raise CustomerValidationError("Fiado não pode ser usado para pagar uma dívida.")
    before = customer_balance(customer)
    amount = money(payload.amount)
    if amount > before:
        raise CustomerValidationError("O pagamento não pode superar o saldo em aberto.")
    payment = CustomerPayment(account_id=user.account_id, customer_id=customer.id, received_by_id=user.id, amount=amount, method=payload.method.value, balance_before=before, balance_after=before - amount, notes=payload.notes)
    db.add(payment)
    db.flush()
    remaining = amount
    debts = sorted((debt for debt in customer.debts if money(debt.balance) > 0 and debt.status != DebtStatus.REVERSED), key=lambda debt: (debt.created_at, debt.id))
    for debt in debts:
        if remaining <= 0: break
        allocated = min(money(debt.balance), remaining)
        debt.balance = money(debt.balance) - allocated
        debt.status = DebtStatus.PAID if money(debt.balance) == 0 else DebtStatus.PARTIAL
        db.add(CustomerPaymentAllocation(payment_id=payment.id, debt_id=debt.id, amount=allocated))
        remaining -= allocated
    register = current_register(db, user)
    if register:
        add_cash_movement(db, register, user, CashMovementType.CREDIT_RECEIPT, amount, payment_method=payload.method.value, reason=f"Recebimento de fiado - {customer.name}", reference_type="customer_payment", reference_id=payment.id)
    return payment


def customer_sales_summary(db: Session, customer: Customer) -> tuple[Decimal, float, object, list[Sale]]:
    sales = db.query(Sale).filter(Sale.account_id == customer.account_id, Sale.customer_id == customer.id, Sale.status == SaleStatus.COMPLETED).order_by(Sale.created_at.desc()).all()
    total = money(sum((money(sale.total) for sale in sales), Decimal("0")))
    average = float(money(total / len(sales))) if sales else 0
    return total, average, sales[0].created_at if sales else None, sales


def debt_is_overdue(debt: CustomerDebt) -> bool:
    return debt.due_date is not None and debt.due_date < local_today() and money(debt.balance) > 0 and debt.status != DebtStatus.REVERSED
