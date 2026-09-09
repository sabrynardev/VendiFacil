from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy.orm import Session

from app.models.cash_register import CashMovement, CashMovementType, CashRegister, CashRegisterStatus
from app.models.sale import PaymentMethod
from app.models.user import User


class CashRegisterValidationError(Exception):
    pass


def money(value) -> Decimal:
    return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def current_register(db: Session, user: User) -> CashRegister | None:
    return db.query(CashRegister).filter(
        CashRegister.account_id == user.account_id,
        CashRegister.opened_by_id == user.id,
        CashRegister.status == CashRegisterStatus.OPEN,
    ).first()


def add_cash_movement(db: Session, register: CashRegister, user: User, movement_type: CashMovementType, amount, **kwargs) -> CashMovement:
    movement = CashMovement(
        account_id=user.account_id,
        cash_register_id=register.id,
        user_id=user.id,
        type=movement_type,
        amount=money(amount),
        **kwargs,
    )
    db.add(movement)
    return movement


def register_summary(register: CashRegister) -> dict[str, float]:
    totals = {method.value: Decimal("0") for method in PaymentMethod}
    supplies = withdrawals = Decimal("0")
    refund_totals = {method.value: Decimal("0") for method in PaymentMethod}
    for movement in register.movements:
        amount = money(movement.amount)
        if movement.type == CashMovementType.SALE and movement.payment_method:
            totals[movement.payment_method] = totals.get(movement.payment_method, Decimal("0")) + amount
        elif movement.type == CashMovementType.SUPPLY:
            supplies += amount
        elif movement.type == CashMovementType.WITHDRAWAL:
            withdrawals += amount
        elif movement.type == CashMovementType.REFUND and movement.payment_method:
            refund_totals[movement.payment_method] = refund_totals.get(movement.payment_method, Decimal("0")) + amount
    net_totals = {method: totals[method] - refund_totals.get(method, Decimal("0")) for method in totals}
    cash_refunds = refund_totals[PaymentMethod.CASH.value]
    expected = money(register.opening_balance) + net_totals[PaymentMethod.CASH.value] + supplies - withdrawals
    return {
        "opening_balance": float(register.opening_balance),
        "cash_sales": float(net_totals[PaymentMethod.CASH.value]),
        "pix_sales": float(net_totals[PaymentMethod.PIX.value]),
        "debit_sales": float(net_totals[PaymentMethod.DEBIT.value]),
        "credit_sales": float(net_totals[PaymentMethod.CREDIT.value]),
        "total_sales": float(sum(net_totals.values())),
        "supplies": float(supplies),
        "withdrawals": float(withdrawals),
        "refunds": float(sum(refund_totals.values())),
        "expected_cash": float(expected),
    }


def open_register(db: Session, user: User, opening_balance: float) -> CashRegister:
    if current_register(db, user):
        raise CashRegisterValidationError("Você já possui um caixa aberto.")
    register = CashRegister(account_id=user.account_id, opened_by_id=user.id, opening_balance=money(opening_balance))
    db.add(register)
    db.flush()
    add_cash_movement(db, register, user, CashMovementType.OPENING, opening_balance, reason="Abertura de caixa")
    return register


def close_register(db: Session, register: CashRegister, user: User, counted_balance: float, note: str | None) -> CashRegister:
    summary = register_summary(register)
    expected = money(summary["expected_cash"])
    counted = money(counted_balance)
    register.expected_balance = expected
    register.counted_balance = counted
    register.difference = counted - expected
    register.closed_by_id = user.id
    register.closed_at = datetime.utcnow()
    register.closing_note = note
    register.status = CashRegisterStatus.CLOSED
    add_cash_movement(db, register, user, CashMovementType.CLOSING, counted, reason=note or "Fechamento de caixa")
    return register
