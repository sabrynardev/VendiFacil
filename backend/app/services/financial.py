import calendar
from datetime import date, datetime, time, timedelta
from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.cash_register import CashMovementType, CashRegister, CashRegisterStatus
from app.models.customer import Customer, CustomerDebt, CustomerPayment, DebtStatus
from app.models.financial import FinancialCategory, FinancialCategoryType, FinancialOrigin, FinancialReceivable, FinancialStatus, ManualRevenue, Payable, PayablePayment, ReceivableReceipt, RecurrenceFrequency, RecurringExpense
from app.models.purchase import PurchaseOrder
from app.models.sale import PaymentMethod, Sale, SaleItem, SalePayment, SaleStatus
from app.models.supplier import Supplier
from app.models.user import User
from app.schemas.financial import FinancialPaymentCreate, ManualRevenueCreate, PayableCreate, ReceivableCreate, RecurringExpenseCreate
from app.services.cash_registers import add_cash_movement, current_register


class FinancialValidationError(Exception):
    pass


def money(value) -> Decimal:
    return Decimal(str(value or 0)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def period_bounds(start: date, end: date) -> tuple[datetime, datetime]:
    if end < start:
        raise FinancialValidationError("A data final deve ser igual ou posterior à data inicial.")
    return datetime.combine(start, time.min), datetime.combine(end, time.max)


def get_category(db: Session, account_id: int, category_id: int, expected_type: FinancialCategoryType) -> FinancialCategory:
    category = db.query(FinancialCategory).filter(
        FinancialCategory.id == category_id,
        FinancialCategory.account_id == account_id,
        FinancialCategory.type == expected_type,
        FinancialCategory.active.is_(True),
    ).first()
    if not category:
        raise FinancialValidationError("Categoria financeira inválida.")
    return category


def payable_status(payable: Payable) -> str:
    if payable.status == FinancialStatus.CANCELLED:
        return FinancialStatus.CANCELLED.value
    if money(payable.paid_amount) >= money(payable.original_amount):
        return FinancialStatus.PAID.value
    if payable.due_date < date.today():
        return "VENCIDA"
    if money(payable.paid_amount) > 0:
        return FinancialStatus.PARTIAL.value
    return FinancialStatus.PENDING.value


def receivable_status(receivable: FinancialReceivable) -> str:
    if receivable.status == FinancialStatus.CANCELLED:
        return FinancialStatus.CANCELLED.value
    if money(receivable.received_amount) >= money(receivable.original_amount):
        return FinancialStatus.PAID.value
    if receivable.due_date < date.today():
        return "VENCIDA"
    if money(receivable.received_amount) > 0:
        return FinancialStatus.PARTIAL.value
    return FinancialStatus.PENDING.value


def create_payable(db: Session, payload: PayableCreate, user: User) -> Payable:
    category = get_category(db, user.account_id, payload.category_id, FinancialCategoryType.EXPENSE)
    amount = money(payload.amount)
    supplier_id = payload.supplier_id
    origin = FinancialOrigin.MANUAL
    reference = None
    affects_result = category.affects_result if payload.affects_result is None else payload.affects_result

    if payload.supplier_id and not db.query(Supplier).filter(Supplier.id == payload.supplier_id, Supplier.account_id == user.account_id).first():
        raise FinancialValidationError("Fornecedor não encontrado.")
    if payload.purchase_order_id:
        order = db.query(PurchaseOrder).filter(PurchaseOrder.id == payload.purchase_order_id, PurchaseOrder.account_id == user.account_id).first()
        if not order:
            raise FinancialValidationError("Pedido de compra não encontrado.")
        if db.query(Payable).filter(Payable.purchase_order_id == order.id).first():
            raise FinancialValidationError("Este pedido já possui uma conta a pagar.")
        amount = money(order.total)
        supplier_id = order.supplier_id
        origin = FinancialOrigin.PURCHASE
        reference = f"Pedido #{order.id:06d}"
        affects_result = False

    payable = Payable(
        account_id=user.account_id,
        category_id=category.id,
        supplier_id=supplier_id,
        purchase_order_id=payload.purchase_order_id,
        created_by_id=user.id,
        description=payload.description,
        original_amount=amount,
        paid_amount=0,
        due_date=payload.due_date,
        notes=payload.notes,
        origin=origin,
        reference=reference,
        affects_result=affects_result,
    )
    db.add(payable)
    db.flush()
    return payable


def register_payable_payment(db: Session, payable: Payable, payload: FinancialPaymentCreate, user: User) -> PayablePayment:
    if payload.idempotency_key:
        duplicate = db.query(PayablePayment).filter(
            PayablePayment.account_id == user.account_id,
            PayablePayment.idempotency_key == payload.idempotency_key,
        ).first()
        if duplicate:
            return duplicate
    if payable.status == FinancialStatus.CANCELLED:
        raise FinancialValidationError("Não é possível pagar uma conta cancelada.")
    balance = money(payable.original_amount) - money(payable.paid_amount)
    amount = money(payload.amount)
    if amount <= 0 or amount > balance:
        raise FinancialValidationError(f"O pagamento deve ser maior que zero e não pode superar o saldo de R$ {balance:.2f}.")
    if payload.method == PaymentMethod.CREDIT_ACCOUNT:
        raise FinancialValidationError("Fiado não é uma forma válida para pagar despesas.")

    register = None
    if payload.use_cash_register:
        if payload.method != PaymentMethod.CASH:
            raise FinancialValidationError("Somente pagamentos em dinheiro podem sair do caixa físico.")
        register = current_register(db, user)
        if not register:
            raise FinancialValidationError("Abra o caixa antes de usar dinheiro do caixa físico.")

    occurred_at = payload.occurred_at or datetime.utcnow()
    payment = PayablePayment(
        account_id=user.account_id,
        payable_id=payable.id,
        user_id=user.id,
        cash_register_id=register.id if register else None,
        amount=amount,
        method=payload.method.value,
        payment_date=occurred_at,
        notes=payload.notes,
        idempotency_key=payload.idempotency_key,
    )
    db.add(payment)
    payable.paid_amount = money(payable.paid_amount) + amount
    payable.payment_method = payload.method.value
    if money(payable.paid_amount) == money(payable.original_amount):
        payable.status = FinancialStatus.PAID
        payable.paid_at = occurred_at
    else:
        payable.status = FinancialStatus.PARTIAL
    if register:
        add_cash_movement(
            db,
            register,
            user,
            CashMovementType.WITHDRAWAL,
            amount,
            payment_method=PaymentMethod.CASH.value,
            reason=f"Pagamento: {payable.description}",
            reference_type="payable",
            reference_id=payable.id,
        )
    db.flush()
    return payment


def create_manual_revenue(db: Session, payload: ManualRevenueCreate, user: User) -> ManualRevenue:
    category = get_category(db, user.account_id, payload.category_id, FinancialCategoryType.REVENUE)
    if payload.payment_method == PaymentMethod.CREDIT_ACCOUNT:
        raise FinancialValidationError("Receita recebida não pode usar a forma fiado.")
    if payload.idempotency_key:
        duplicate = db.query(ManualRevenue).filter(
            ManualRevenue.account_id == user.account_id,
            ManualRevenue.idempotency_key == payload.idempotency_key,
        ).first()
        if duplicate:
            return duplicate
    revenue = ManualRevenue(
        account_id=user.account_id,
        category_id=category.id,
        created_by_id=user.id,
        description=payload.description,
        amount=money(payload.amount),
        received_at=payload.received_at or datetime.utcnow(),
        competence_date=payload.competence_date,
        payment_method=payload.payment_method.value,
        reference=payload.reference,
        notes=payload.notes,
        idempotency_key=payload.idempotency_key,
    )
    db.add(revenue)
    db.flush()
    return revenue


def create_receivable(db: Session, payload: ReceivableCreate, user: User) -> FinancialReceivable:
    category = get_category(db, user.account_id, payload.category_id, FinancialCategoryType.REVENUE)
    if payload.customer_id and not db.query(Customer).filter(Customer.id == payload.customer_id, Customer.account_id == user.account_id).first():
        raise FinancialValidationError("Cliente não encontrado.")
    receivable = FinancialReceivable(
        account_id=user.account_id,
        category_id=category.id,
        customer_id=payload.customer_id,
        created_by_id=user.id,
        description=payload.description,
        original_amount=money(payload.amount),
        received_amount=0,
        due_date=payload.due_date,
        notes=payload.notes,
    )
    db.add(receivable)
    db.flush()
    return receivable


def register_receivable_receipt(db: Session, receivable: FinancialReceivable, payload: FinancialPaymentCreate, user: User) -> ReceivableReceipt:
    if payload.idempotency_key:
        duplicate = db.query(ReceivableReceipt).filter(
            ReceivableReceipt.account_id == user.account_id,
            ReceivableReceipt.idempotency_key == payload.idempotency_key,
        ).first()
        if duplicate:
            return duplicate
    if receivable.status == FinancialStatus.CANCELLED:
        raise FinancialValidationError("Não é possível receber uma conta cancelada.")
    balance = money(receivable.original_amount) - money(receivable.received_amount)
    amount = money(payload.amount)
    if amount <= 0 or amount > balance:
        raise FinancialValidationError(f"O recebimento não pode superar o saldo de R$ {balance:.2f}.")
    if payload.method == PaymentMethod.CREDIT_ACCOUNT:
        raise FinancialValidationError("Fiado não é uma forma válida de recebimento.")
    receipt = ReceivableReceipt(
        account_id=user.account_id,
        receivable_id=receivable.id,
        user_id=user.id,
        amount=amount,
        method=payload.method.value,
        received_at=payload.occurred_at or datetime.utcnow(),
        notes=payload.notes,
        idempotency_key=payload.idempotency_key,
    )
    db.add(receipt)
    receivable.received_amount = money(receivable.received_amount) + amount
    receivable.status = FinancialStatus.PAID if money(receivable.received_amount) == money(receivable.original_amount) else FinancialStatus.PARTIAL
    db.flush()
    return receipt


def _next_recurrence(current: date, frequency: RecurrenceFrequency) -> date:
    if frequency == RecurrenceFrequency.WEEKLY:
        return current + timedelta(days=7)
    if frequency == RecurrenceFrequency.YEARLY:
        year = current.year + 1
        return current.replace(year=year, day=min(current.day, calendar.monthrange(year, current.month)[1]))
    month = 1 if current.month == 12 else current.month + 1
    year = current.year + 1 if current.month == 12 else current.year
    return current.replace(year=year, month=month, day=min(current.day, calendar.monthrange(year, month)[1]))


def create_recurring_expense(db: Session, payload: RecurringExpenseCreate, user: User) -> RecurringExpense:
    get_category(db, user.account_id, payload.category_id, FinancialCategoryType.EXPENSE)
    recurring = RecurringExpense(account_id=user.account_id, created_by_id=user.id, **payload.model_dump())
    db.add(recurring)
    db.flush()
    return recurring


def generate_recurring_payables(db: Session, user: User, through: date) -> list[Payable]:
    generated = []
    recurring_items = db.query(RecurringExpense).filter(
        RecurringExpense.account_id == user.account_id,
        RecurringExpense.active.is_(True),
        RecurringExpense.next_due_date <= through,
    ).with_for_update().all()
    for recurring in recurring_items:
        while recurring.next_due_date <= through:
            period = recurring.next_due_date.isoformat()
            exists = db.query(Payable).filter(Payable.recurrence_id == recurring.id, Payable.recurrence_period == period).first()
            if not exists:
                payable = Payable(
                    account_id=user.account_id,
                    category_id=recurring.category_id,
                    supplier_id=recurring.supplier_id,
                    created_by_id=user.id,
                    description=recurring.description,
                    original_amount=money(recurring.amount),
                    paid_amount=0,
                    due_date=recurring.next_due_date,
                    notes=recurring.notes,
                    origin=FinancialOrigin.RECURRING,
                    affects_result=recurring.category.affects_result,
                    recurrence_id=recurring.id,
                    recurrence_period=period,
                )
                db.add(payable)
                generated.append(payable)
            recurring.next_due_date = _next_recurrence(recurring.next_due_date, recurring.frequency)
    db.flush()
    return generated


def financial_summary(db: Session, account_id: int, start: date, end: date) -> dict:
    start_at, end_at = period_bounds(start, end)
    sales = db.query(Sale).filter(Sale.account_id == account_id, Sale.status == SaleStatus.COMPLETED, Sale.created_at.between(start_at, end_at))
    revenue = money(sales.with_entities(func.coalesce(func.sum(Sale.total), 0)).scalar())
    sales_count = int(sales.with_entities(func.count(Sale.id)).scalar() or 0)

    payment_rows = db.query(SalePayment.method, func.coalesce(func.sum(SalePayment.amount), 0)).join(Sale).filter(
        Sale.account_id == account_id,
        Sale.status == SaleStatus.COMPLETED,
        Sale.created_at.between(start_at, end_at),
    ).group_by(SalePayment.method).all()
    payment_methods = {method.value if hasattr(method, "value") else str(method): float(money(total)) for method, total in payment_rows}
    credit_sales = money(payment_methods.get(PaymentMethod.CREDIT_ACCOUNT.value, 0))
    received_sales = money(sum((money(value) for key, value in payment_methods.items() if key != PaymentMethod.CREDIT_ACCOUNT.value), Decimal("0")))

    cmv = money(db.query(func.coalesce(func.sum(SaleItem.quantity * SaleItem.cost_price), 0)).join(Sale).filter(
        Sale.account_id == account_id,
        Sale.status == SaleStatus.COMPLETED,
        Sale.created_at.between(start_at, end_at),
    ).scalar())
    credit_receipts = money(db.query(func.coalesce(func.sum(CustomerPayment.amount), 0)).filter(
        CustomerPayment.account_id == account_id,
        CustomerPayment.created_at.between(start_at, end_at),
    ).scalar())
    manual_revenues = money(db.query(func.coalesce(func.sum(ManualRevenue.amount), 0)).filter(
        ManualRevenue.account_id == account_id,
        ManualRevenue.cancelled_at.is_(None),
        ManualRevenue.received_at.between(start_at, end_at),
    ).scalar())
    payable_payments = money(db.query(func.coalesce(func.sum(PayablePayment.amount), 0)).filter(
        PayablePayment.account_id == account_id,
        PayablePayment.payment_date.between(start_at, end_at),
    ).scalar())
    operational_expenses = money(db.query(func.coalesce(func.sum(PayablePayment.amount), 0)).join(Payable).filter(
        PayablePayment.account_id == account_id,
        Payable.affects_result.is_(True),
        PayablePayment.payment_date.between(start_at, end_at),
    ).scalar())
    manual_receipts = money(db.query(func.coalesce(func.sum(ReceivableReceipt.amount), 0)).filter(
        ReceivableReceipt.account_id == account_id,
        ReceivableReceipt.received_at.between(start_at, end_at),
    ).scalar())

    gross_profit = money(revenue - cmv)
    gross_margin = money(gross_profit / revenue * 100) if revenue else Decimal("0")
    payables_balance = money(db.query(func.coalesce(func.sum(Payable.original_amount - Payable.paid_amount), 0)).filter(Payable.account_id == account_id, Payable.status != FinancialStatus.CANCELLED).scalar())
    debt_balance = money(db.query(func.coalesce(func.sum(CustomerDebt.balance), 0)).filter(CustomerDebt.account_id == account_id, CustomerDebt.status.in_([DebtStatus.OPEN, DebtStatus.PARTIAL])).scalar())
    other_receivables = money(db.query(func.coalesce(func.sum(FinancialReceivable.original_amount - FinancialReceivable.received_amount), 0)).filter(FinancialReceivable.account_id == account_id, FinancialReceivable.status != FinancialStatus.CANCELLED).scalar())
    overdue_payables = money(sum((money(item.original_amount) - money(item.paid_amount) for item in db.query(Payable).filter(Payable.account_id == account_id, Payable.status != FinancialStatus.CANCELLED, Payable.due_date < date.today()).all()), Decimal("0")))
    overdue_debts = money(db.query(func.coalesce(func.sum(CustomerDebt.balance), 0)).filter(CustomerDebt.account_id == account_id, CustomerDebt.status.in_([DebtStatus.OPEN, DebtStatus.PARTIAL]), CustomerDebt.due_date.is_not(None), CustomerDebt.due_date < date.today()).scalar())
    overdue_manual = money(sum((money(item.original_amount) - money(item.received_amount) for item in db.query(FinancialReceivable).filter(FinancialReceivable.account_id == account_id, FinancialReceivable.status != FinancialStatus.CANCELLED, FinancialReceivable.due_date < date.today()).all()), Decimal("0")))

    return {
        "period_start": start,
        "period_end": end,
        "revenue": float(revenue),
        "sales_count": sales_count,
        "average_ticket": float(money(revenue / sales_count) if sales_count else 0),
        "received_sales": float(received_sales),
        "credit_sales": float(credit_sales),
        "credit_receipts": float(credit_receipts),
        "manual_revenues": float(manual_revenues),
        "cash_in": float(money(received_sales + credit_receipts + manual_revenues + manual_receipts)),
        "cmv": float(cmv),
        "gross_profit": float(gross_profit),
        "gross_margin": float(gross_margin),
        "operational_expenses": float(operational_expenses),
        "cash_out": float(payable_payments),
        "estimated_result": float(money(gross_profit - operational_expenses)),
        "payables_balance": float(payables_balance),
        "receivables_balance": float(money(debt_balance + other_receivables)),
        "overdue_payables": float(overdue_payables),
        "overdue_receivables": float(money(overdue_debts + overdue_manual)),
        "payment_methods": payment_methods,
    }


def cash_flow(db: Session, account_id: int, start: date, end: date) -> list[dict]:
    start_at, end_at = period_bounds(start, end)
    entries = []
    sale_payments = db.query(SalePayment).join(Sale).filter(
        Sale.account_id == account_id,
        Sale.status == SaleStatus.COMPLETED,
        SalePayment.method != PaymentMethod.CREDIT_ACCOUNT,
        SalePayment.confirmed_at.between(start_at, end_at),
    ).all()
    for item in sale_payments:
        entries.append({"id": f"sale-{item.id}", "occurred_at": item.confirmed_at, "direction": "ENTRADA", "source": "VENDA", "description": f"Venda #{item.sale_id:06d}", "amount": float(item.amount), "payment_method": item.method.value})
    for item in db.query(CustomerPayment).filter(CustomerPayment.account_id == account_id, CustomerPayment.created_at.between(start_at, end_at)).all():
        entries.append({"id": f"credit-{item.id}", "occurred_at": item.created_at, "direction": "ENTRADA", "source": "RECEBIMENTO_FIADO", "description": f"Recebimento de {item.customer.name}", "amount": float(item.amount), "payment_method": item.method})
    for item in db.query(ManualRevenue).filter(ManualRevenue.account_id == account_id, ManualRevenue.cancelled_at.is_(None), ManualRevenue.received_at.between(start_at, end_at)).all():
        entries.append({"id": f"revenue-{item.id}", "occurred_at": item.received_at, "direction": "ENTRADA", "source": "RECEITA_MANUAL", "description": item.description, "amount": float(item.amount), "payment_method": item.payment_method})
    for item in db.query(ReceivableReceipt).filter(ReceivableReceipt.account_id == account_id, ReceivableReceipt.received_at.between(start_at, end_at)).all():
        entries.append({"id": f"receivable-{item.id}", "occurred_at": item.received_at, "direction": "ENTRADA", "source": "CONTA_RECEBER", "description": item.receivable.description, "amount": float(item.amount), "payment_method": item.method})
    for item in db.query(PayablePayment).filter(PayablePayment.account_id == account_id, PayablePayment.payment_date.between(start_at, end_at)).all():
        entries.append({"id": f"payable-{item.id}", "occurred_at": item.payment_date, "direction": "SAIDA", "source": "CONTA_PAGAR", "description": item.payable.description, "amount": float(item.amount), "payment_method": item.method})
    return sorted(entries, key=lambda entry: entry["occurred_at"], reverse=True)


def projections(db: Session, account_id: int, days: int) -> dict:
    start = date.today()
    end = start + timedelta(days=days)
    payables = money(db.query(func.coalesce(func.sum(Payable.original_amount - Payable.paid_amount), 0)).filter(
        Payable.account_id == account_id,
        Payable.status.notin_([FinancialStatus.PAID, FinancialStatus.CANCELLED]),
        Payable.due_date.between(start, end),
    ).scalar())
    customer_debts = money(db.query(func.coalesce(func.sum(CustomerDebt.balance), 0)).filter(
        CustomerDebt.account_id == account_id,
        CustomerDebt.status.in_([DebtStatus.OPEN, DebtStatus.PARTIAL]),
        CustomerDebt.due_date.is_not(None),
        CustomerDebt.due_date.between(start, end),
    ).scalar())
    manual = money(db.query(func.coalesce(func.sum(FinancialReceivable.original_amount - FinancialReceivable.received_amount), 0)).filter(
        FinancialReceivable.account_id == account_id,
        FinancialReceivable.status.notin_([FinancialStatus.PAID, FinancialStatus.CANCELLED]),
        FinancialReceivable.due_date.between(start, end),
    ).scalar())
    return {"days": days, "payables": float(payables), "receivables": float(money(customer_debts + manual))}


def reconciliation_issues(db: Session, account_id: int) -> list[dict]:
    issues = []
    sales_without_payments = db.query(Sale).filter(
        Sale.account_id == account_id,
        Sale.status == SaleStatus.COMPLETED,
        ~Sale.payments.any(),
    ).all()
    for sale in sales_without_payments:
        issues.append({"code": "SALE_WITHOUT_PAYMENT", "description": f"Venda #{sale.id:06d} concluída sem pagamento correspondente.", "reference_id": sale.id, "severity": "ALTA"})
    payments_without_allocation = db.query(CustomerPayment).filter(
        CustomerPayment.account_id == account_id,
        ~CustomerPayment.allocations.any(),
    ).all()
    for payment in payments_without_allocation:
        issues.append({"code": "CREDIT_WITHOUT_REFERENCE", "description": f"Recebimento de fiado #{payment.id} sem alocação de dívida.", "reference_id": payment.id, "severity": "ALTA"})
    for register in db.query(CashRegister).filter(CashRegister.account_id == account_id, CashRegister.status == CashRegisterStatus.CLOSED).all():
        if register.difference is not None and abs(float(register.difference)) >= 5:
            issues.append({"code": "CASH_DIFFERENCE", "description": f"Caixa #{register.id} fechado com diferença de R$ {float(register.difference):.2f}.", "reference_id": register.id, "severity": "MEDIA"})
    orders_with_receipt = db.query(PurchaseOrder).filter(PurchaseOrder.account_id == account_id, PurchaseOrder.receipts.any()).all()
    for order in orders_with_receipt:
        if not db.query(Payable).filter(Payable.purchase_order_id == order.id).first():
            issues.append({"code": "PURCHASE_WITHOUT_PAYABLE", "description": f"Pedido #{order.id:06d} recebido sem obrigação financeira definida.", "reference_id": order.id, "severity": "BAIXA"})
    return issues
