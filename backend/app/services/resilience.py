import json
import time
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy.orm import Session

from app.core.permissions import PermissionCode
from app.core.products import ProductUnit
from app.models.cash_register import CashMovementType, CashRegister
from app.models.product import Product
from app.models.resilience import SyncOperationLog
from app.models.sale import PaymentMethod, Sale, SaleItem, SalePayment, SaleStatus
from app.models.stock_movement import StockMovementType
from app.models.user import User
from app.schemas.sale import OfflineSaleCreate
from app.services.audit import log_audit
from app.services.cash_registers import add_cash_movement
from app.services.inventory import apply_stock_movement
from app.services.profiles import permission_codes_for_user
from app.services.sales import money


class SyncValidationError(Exception):
    def __init__(self, message: str, category: str = "VALIDATION"):
        super().__init__(message)
        self.category = category


def _safe_error(message: str) -> str:
    return message.replace("\n", " ")[:255]


def _naive_utc(value: datetime) -> datetime:
    return value.astimezone(timezone.utc).replace(tzinfo=None) if value.tzinfo is not None else value


def record_sync_failure(db: Session, payload: OfflineSaleCreate, user: User, error: SyncValidationError, duration_ms: int) -> SyncOperationLog:
    entry = db.query(SyncOperationLog).filter(SyncOperationLog.account_id == user.account_id, SyncOperationLog.operation_id == payload.operation_id).first()
    if not entry:
        entry = SyncOperationLog(account_id=user.account_id, user_id=user.id, operation_id=payload.operation_id, operation_type="SALE", device_id=payload.device_id, status="REQUIRES_ATTENTION")
        db.add(entry)
    entry.attempts = int(entry.attempts or 0) + 1
    entry.status = "REQUIRES_ATTENTION"
    entry.error_category = error.category
    entry.error_message = _safe_error(str(error))
    entry.duration_ms = duration_ms
    return entry


def sync_offline_sale(db: Session, payload: OfflineSaleCreate, user: User) -> tuple[Sale, bool, list[str]]:
    started = time.perf_counter()
    duplicate = db.query(Sale).filter(Sale.account_id == user.account_id, Sale.offline_operation_id == payload.operation_id).first()
    if not duplicate:
        duplicate = db.query(Sale).filter(Sale.account_id == user.account_id, Sale.idempotency_key == payload.idempotency_key).first()
    if duplicate:
        return duplicate, True, json.loads(duplicate.sync_conflict) if duplicate.sync_conflict else []

    permissions = set(permission_codes_for_user(user))
    if PermissionCode.CASHIER_OPERATE.value not in permissions:
        raise SyncValidationError("A permissão para realizar vendas não está mais disponível. Solicite revisão de um gerente.", "AUTHORIZATION")
    local_time = payload.local_created_at
    local_time = _naive_utc(local_time)
    age = datetime.utcnow() - local_time
    if age > timedelta(hours=12) or age < timedelta(minutes=-5):
        raise SyncValidationError("A autorização offline expirou. Solicite revisão de um gerente.", "OFFLINE_SESSION_EXPIRED")
    if any(payment.method == PaymentMethod.CREDIT_ACCOUNT for payment in payload.payments):
        raise SyncValidationError("Venda fiada exige conexão para validar saldo e limite do cliente.", "ONLINE_REQUIRED")

    register = None
    conflicts = []
    if payload.cash_register_id:
        register = db.query(CashRegister).filter(CashRegister.id == payload.cash_register_id, CashRegister.account_id == user.account_id).first()
    if not register:
        conflicts.append("CAIXA_NAO_ENCONTRADO")
    elif register.opened_by_id != user.id:
        raise SyncValidationError("O caixa informado pertence a outro operador.", "CASH_REGISTER_CONFLICT")
    elif register.status.value != "OPEN":
        conflicts.append("CAIXA_JA_FECHADO")

    prepared = []
    subtotal = Decimal("0")
    gross_total = Decimal("0")
    for item in payload.items:
        product = db.query(Product).filter(Product.id == item.product_id, Product.account_id == user.account_id).with_for_update().first()
        if not product:
            raise SyncValidationError(f"O produto {item.product_id} não existe mais. A venda permanece na fila para revisão.", "PRODUCT_NOT_FOUND")
        quantity = Decimal(str(item.quantity))
        if product.unit == ProductUnit.UN.value and quantity != quantity.to_integral_value():
            raise SyncValidationError(f"{product.name} deve ser vendido em unidades inteiras.")
        unit_price = money(item.unit_price)
        gross = money(unit_price * quantity)
        discount = money(item.discount)
        if discount > gross:
            raise SyncValidationError(f"O desconto de {product.name} supera o valor do item.")
        if not product.active:
            conflicts.append(f"PRODUTO_INATIVO:{product.id}")
        if money(product.sale_price) != unit_price:
            cached_version = _naive_utc(item.product_updated_at) if item.product_updated_at else None
            if cached_version is None or cached_version >= product.updated_at:
                raise SyncValidationError(f"O preço offline de {product.name} não corresponde à versão do catálogo e requer revisão.", "PRICE_INTEGRITY")
            conflicts.append(f"PRECO_ALTERADO:{product.id}")
        if Decimal(str(product.stock_quantity)) < quantity:
            conflicts.append(f"ESTOQUE_NEGATIVO:{product.id}")
        item_total = money(gross - discount)
        gross_total += gross
        subtotal += item_total
        prepared.append((product, quantity, unit_price, money(product.cost_price), discount, item_total))

    global_discount = money(payload.discount)
    surcharge = money(payload.surcharge)
    total = money(subtotal - global_discount + surcharge)
    if total < 0:
        raise SyncValidationError("O desconto geral não pode gerar total negativo.")
    discount_percent = (sum((entry[4] for entry in prepared), Decimal("0")) + global_discount) / gross_total * 100 if gross_total else Decimal("0")
    if discount_percent > Decimal("10") or (discount_percent > 0 and PermissionCode.DISCOUNT_NORMAL.value not in permissions):
        raise SyncValidationError("Este desconto exige autorização online de gerente.", "ONLINE_REQUIRED")
    if money(sum((money(payment.amount) for payment in payload.payments), Decimal("0"))) != total:
        raise SyncValidationError("A soma dos pagamentos não corresponde ao total da venda.")

    total_received = Decimal("0")
    total_change = Decimal("0")
    for payment in payload.payments:
        amount = money(payment.amount)
        received = money(payment.amount_received if payment.amount_received is not None else amount)
        if payment.method == PaymentMethod.CASH:
            if received < amount:
                raise SyncValidationError("Valor recebido em dinheiro é insuficiente.")
            total_change += received - amount
        elif payment.amount_received is not None and received != amount:
            raise SyncValidationError("PIX e cartões devem registrar exatamente o valor informado.")
        total_received += received

    sale = Sale(account_id=user.account_id, user_id=user.id, cash_register_id=register.id if register else None, subtotal=money(subtotal), discount=global_discount, surcharge=surcharge, total=total, payment_method="+".join(payment.method.value for payment in payload.payments), amount_received=total_received, change_amount=total_change, status=SaleStatus.COMPLETED, note=payload.note, idempotency_key=payload.idempotency_key, offline_operation_id=payload.operation_id, device_id=payload.device_id, local_created_at=local_time, sync_status="SYNCED_WITH_CONFLICT" if conflicts else "SYNCED", sync_conflict=json.dumps(conflicts) if conflicts else None)
    db.add(sale)
    db.flush()
    for product, quantity, unit_price, cost_price, discount, item_total in prepared:
        db.add(SaleItem(sale_id=sale.id, product_id=product.id, quantity=quantity, unit_price=unit_price, cost_price=cost_price, discount=discount, subtotal=item_total))
        apply_stock_movement(db, product=product, user=user, movement_type=StockMovementType.VENDA, quantity=float(quantity), reason=f"Venda offline #{sale.id} ({payload.device_id})", reference_type="sale", reference_id=sale.id, allow_negative=True)
    for payment in payload.payments:
        amount = money(payment.amount)
        received = money(payment.amount_received if payment.amount_received is not None else amount)
        change = received - amount if payment.method == PaymentMethod.CASH else Decimal("0")
        db.add(SalePayment(sale_id=sale.id, method=payment.method, amount=amount, amount_received=received, change_amount=change))
        if register:
            add_cash_movement(db, register, user, CashMovementType.SALE, amount, payment_method=payment.method.value, reason=f"Venda offline #{sale.id}", reference_type="sale", reference_id=sale.id)
    duration = int((time.perf_counter() - started) * 1000)
    db.add(SyncOperationLog(account_id=user.account_id, user_id=user.id, operation_id=payload.operation_id, operation_type="SALE", device_id=payload.device_id, status="SYNCED_WITH_CONFLICT" if conflicts else "SYNCED", attempts=1, conflict=bool(conflicts), duration_ms=duration))
    log_audit(db, user, action="OFFLINE_SYNC", entity_type="SALE", entity_id=sale.id, description=f"Sincronizou venda offline do terminal {payload.device_id}.", changes={"operation_id": payload.operation_id, "conflicts": conflicts})
    db.flush()
    return sale, False, conflicts
