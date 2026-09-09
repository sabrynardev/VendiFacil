from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP

from sqlalchemy.orm import Session

from app.auth.security import verify_password
from app.core.permissions import PermissionCode
from app.core.products import ProductUnit
from app.models.cash_register import CashMovementType
from app.models.customer import Customer, CustomerDebt, DebtStatus
from app.models.product import Product
from app.models.sale import PaymentMethod, Sale, SaleItem, SalePayment, SaleStatus
from app.models.stock_movement import StockMovementType
from app.models.user import User
from app.schemas.sale import HoldSaleCreate, PaymentCreate, SaleCreate
from app.services.cash_registers import add_cash_movement, current_register
from app.services.customers import customer_balance
from app.services.inventory import StockValidationError, apply_stock_movement
from app.services.profiles import permission_codes_for_user


class SaleValidationError(Exception):
    pass


def money(value) -> Decimal:
    return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def prepare_items(db: Session, items, user: User, *, check_stock: bool = True) -> tuple[list[dict], Decimal]:
    prepared = []
    subtotal = Decimal("0")
    for item in items:
        product = db.query(Product).filter(
            Product.id == item.product_id,
            Product.account_id == user.account_id,
            Product.active.is_(True),
        ).with_for_update().first()
        if not product:
            raise SaleValidationError("Produto não encontrado.")
        quantity = Decimal(str(item.quantity))
        if product.unit == ProductUnit.UN.value and quantity != quantity.to_integral_value():
            raise SaleValidationError(f"{product.name} deve ser vendido em unidades inteiras.")
        available = Decimal(str(product.stock_quantity))
        if check_stock and available < quantity:
            raise SaleValidationError(f"Estoque insuficiente para {product.name}. Disponível: {float(available):g} {product.unit}.")
        gross = money(Decimal(str(product.sale_price)) * quantity)
        discount = money(item.discount)
        if discount > gross:
            raise SaleValidationError(f"O desconto de {product.name} não pode superar o valor do item.")
        item_total = money(gross - discount)
        subtotal += item_total
        prepared.append({"product": product, "quantity": quantity, "unit_price": money(product.sale_price), "cost_price": money(product.cost_price), "discount": discount, "subtotal": item_total})
    return prepared, money(subtotal)


def validate_discount_authorization(db: Session, payload: SaleCreate, user: User, gross_total: Decimal, total_discount: Decimal) -> User | None:
    if total_discount <= 0 or gross_total <= 0:
        return None
    discount_percent = total_discount / gross_total * 100
    user_permissions = permission_codes_for_user(user)
    if discount_percent <= Decimal("10") and PermissionCode.DISCOUNT_NORMAL.value in user_permissions:
        return None
    if PermissionCode.DISCOUNT_SPECIAL.value in user_permissions:
        return user
    if not payload.authorization_email or not payload.authorization_password:
        raise SaleValidationError("Desconto acima de 10% exige autorização de gerente ou administrador.")
    authorizer = db.query(User).filter(
        User.account_id == user.account_id,
        User.email == payload.authorization_email,
        User.active.is_(True),
    ).first()
    if not authorizer or not verify_password(payload.authorization_password, authorizer.password_hash):
        raise SaleValidationError("Credenciais de autorização inválidas.")
    if PermissionCode.DISCOUNT_SPECIAL.value not in permission_codes_for_user(authorizer):
        raise SaleValidationError("O usuário informado não pode autorizar desconto especial.")
    return authorizer


def normalized_payments(payload: SaleCreate, total: Decimal) -> list[PaymentCreate]:
    if payload.payments:
        return payload.payments
    return [PaymentCreate(method=payload.payment_method, amount=float(total), amount_received=payload.amount_received)]


def validate_credit_sale(db: Session, payload: SaleCreate, payments: list[PaymentCreate], user: User) -> tuple[Customer | None, Decimal, User | None]:
    credit_amount = money(sum((money(payment.amount) for payment in payments if payment.method == PaymentMethod.CREDIT_ACCOUNT), Decimal("0")))
    if credit_amount <= 0:
        customer = db.query(Customer).filter(Customer.id == payload.customer_id, Customer.account_id == user.account_id).first() if payload.customer_id else None
        if payload.customer_id and not customer:
            raise SaleValidationError("Cliente não encontrado.")
        return customer, credit_amount, None
    if PermissionCode.CREDIT_SELL.value not in permission_codes_for_user(user):
        raise SaleValidationError("Você não possui permissão para realizar venda fiada.")
    if not payload.customer_id:
        raise SaleValidationError("Selecione um cliente para realizar venda fiada.")
    customer = db.query(Customer).filter(Customer.id == payload.customer_id, Customer.account_id == user.account_id, Customer.active.is_(True)).with_for_update().first()
    if not customer:
        raise SaleValidationError("Cliente não encontrado.")
    if customer.credit_blocked:
        raise SaleValidationError("O fiado deste cliente está bloqueado.")
    projected = customer_balance(customer) + credit_amount
    if customer.credit_limit is None or projected <= money(customer.credit_limit):
        return customer, credit_amount, None
    permissions = permission_codes_for_user(user)
    if PermissionCode.CREDIT_MANAGE.value in permissions:
        return customer, credit_amount, user
    if not payload.authorization_email or not payload.authorization_password:
        raise SaleValidationError("O limite de crédito será excedido. Solicite autorização de gerente ou administrador.")
    authorizer = db.query(User).filter(User.account_id == user.account_id, User.email == payload.authorization_email, User.active.is_(True)).first()
    if not authorizer or not verify_password(payload.authorization_password, authorizer.password_hash) or PermissionCode.CREDIT_MANAGE.value not in permission_codes_for_user(authorizer):
        raise SaleValidationError("Credenciais de autorização de crédito inválidas.")
    return customer, credit_amount, authorizer


def create_sale(db: Session, payload: SaleCreate, user: User, existing_sale: Sale | None = None) -> tuple[Sale, User | None]:
    register = current_register(db, user)
    if not register:
        raise SaleValidationError("Abra o caixa antes de finalizar uma venda.")
    if payload.idempotency_key:
        duplicate = db.query(Sale).filter(Sale.account_id == user.account_id, Sale.idempotency_key == payload.idempotency_key).first()
        if duplicate:
            return duplicate, None

    prepared_items, item_subtotal = prepare_items(db, payload.items, user)
    item_discounts = sum((entry["discount"] for entry in prepared_items), Decimal("0"))
    global_discount = money(payload.discount)
    surcharge = money(payload.surcharge)
    total = money(item_subtotal - global_discount + surcharge)
    if total < 0:
        raise SaleValidationError("O desconto geral não pode gerar total negativo.")
    gross_total = money(sum((entry["unit_price"] * entry["quantity"] for entry in prepared_items), Decimal("0")))
    authorizer = validate_discount_authorization(db, payload, user, gross_total, item_discounts + global_discount)

    payments = normalized_payments(payload, total)
    if money(sum((money(payment.amount) for payment in payments), Decimal("0"))) != total:
        raise SaleValidationError("A soma dos pagamentos deve ser igual ao total da venda.")
    customer, credit_amount, credit_authorizer = validate_credit_sale(db, payload, payments, user)

    total_received = Decimal("0")
    total_change = Decimal("0")
    for payment in payments:
        amount = money(payment.amount)
        received = money(payment.amount_received if payment.amount_received is not None else amount)
        if payment.method == PaymentMethod.CASH:
            if received < amount:
                raise SaleValidationError("Valor recebido em dinheiro é insuficiente.")
            total_change += received - amount
        elif payment.amount_received is not None and received != amount:
            raise SaleValidationError("PIX e cartões devem registrar exatamente o valor informado.")
        total_received += received

    sale = existing_sale or Sale(account_id=user.account_id, user_id=user.id)
    if existing_sale:
        if sale.status != SaleStatus.ON_HOLD:
            raise SaleValidationError("Esta venda não está em espera.")
        sale.items.clear()
    else:
        db.add(sale)
    sale.cash_register_id = register.id
    sale.customer_id = customer.id if customer else None
    sale.subtotal = item_subtotal
    sale.discount = global_discount
    sale.surcharge = surcharge
    sale.total = total
    sale.payment_method = "+".join(payment.method.value for payment in payments)
    sale.amount_received = total_received
    sale.change_amount = total_change
    sale.note = payload.note
    sale.idempotency_key = payload.idempotency_key
    sale.credit_due_date = payload.credit_due_date
    sale.credit_authorized_by_id = credit_authorizer.id if credit_authorizer else None
    sale.status = SaleStatus.COMPLETED
    db.flush()

    for entry in prepared_items:
        db.add(SaleItem(sale_id=sale.id, product_id=entry["product"].id, quantity=entry["quantity"], unit_price=entry["unit_price"], cost_price=entry["cost_price"], discount=entry["discount"], subtotal=entry["subtotal"]))
        try:
            apply_stock_movement(db, product=entry["product"], user=user, movement_type=StockMovementType.VENDA, quantity=float(entry["quantity"]), reason=f"Venda #{sale.id}", reference_type="sale", reference_id=sale.id)
        except StockValidationError as exc:
            raise SaleValidationError(str(exc)) from exc

    for payment in payments:
        amount = money(payment.amount)
        received = money(payment.amount_received if payment.amount_received is not None else amount)
        change = received - amount if payment.method == PaymentMethod.CASH else Decimal("0")
        db.add(SalePayment(sale_id=sale.id, method=payment.method, amount=amount, amount_received=received, change_amount=change))
        if payment.method != PaymentMethod.CREDIT_ACCOUNT:
            add_cash_movement(db, register, user, CashMovementType.SALE, amount, payment_method=payment.method.value, reason=f"Venda #{sale.id}", reference_type="sale", reference_id=sale.id)
    if customer and credit_amount > 0:
        db.add(CustomerDebt(account_id=user.account_id, customer_id=customer.id, sale_id=sale.id, amount=credit_amount, balance=credit_amount, due_date=payload.credit_due_date, status=DebtStatus.OPEN, notes=payload.note))
    db.flush()
    return sale, authorizer


def hold_sale(db: Session, payload: HoldSaleCreate, user: User) -> Sale:
    prepared, subtotal = prepare_items(db, payload.items, user, check_stock=False)
    total = money(subtotal - money(payload.discount) + money(payload.surcharge))
    if total < 0:
        raise SaleValidationError("O desconto não pode gerar total negativo.")
    customer = db.query(Customer).filter(Customer.id == payload.customer_id, Customer.account_id == user.account_id).first() if payload.customer_id else None
    sale = Sale(account_id=user.account_id, user_id=user.id, customer_id=customer.id if customer else None, subtotal=subtotal, discount=money(payload.discount), surcharge=money(payload.surcharge), total=total, payment_method="PENDENTE", status=SaleStatus.ON_HOLD, note=payload.note)
    db.add(sale)
    db.flush()
    for entry in prepared:
        db.add(SaleItem(sale_id=sale.id, product_id=entry["product"].id, quantity=entry["quantity"], unit_price=entry["unit_price"], discount=entry["discount"], subtotal=entry["subtotal"]))
    return sale


def cancel_sale(db: Session, sale: Sale, user: User, reason: str) -> None:
    if sale.status == SaleStatus.CANCELLED:
        raise SaleValidationError("Esta venda já foi cancelada.")
    if sale.status == SaleStatus.ON_HOLD:
        sale.status = SaleStatus.CANCELLED
    else:
        if not sale.cash_register or sale.cash_register.status.value != "OPEN":
            raise SaleValidationError("O caixa da venda precisa estar aberto para registrar o estorno.")
        for item in sale.items:
            apply_stock_movement(db, product=item.product, user=user, movement_type=StockMovementType.CANCELAMENTO, quantity=float(item.quantity), reason=f"Cancelamento da venda #{sale.id}", reference_type="sale", reference_id=sale.id)
        for payment in sale.payments:
            if payment.method != PaymentMethod.CREDIT_ACCOUNT:
                add_cash_movement(db, sale.cash_register, user, CashMovementType.REFUND, payment.amount, payment_method=payment.method.value, reason=reason, reference_type="sale", reference_id=sale.id)
        if sale.customer_debt:
            sale.customer_debt.balance = 0
            sale.customer_debt.status = DebtStatus.REVERSED
        sale.status = SaleStatus.CANCELLED
    sale.cancelled_at = datetime.utcnow()
    sale.cancelled_by_id = user.id
    sale.cancellation_reason = reason
