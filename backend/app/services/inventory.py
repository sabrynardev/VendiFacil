from datetime import datetime, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.product import Product
from app.models.sale import Sale, SaleItem, SaleStatus
from app.models.stock_movement import StockMovement, StockMovementType
from app.models.user import User
from app.core.products import ProductUnit


class StockValidationError(Exception):
    pass


INBOUND_MOVEMENTS = {
    StockMovementType.ENTRADA,
    StockMovementType.DEVOLUCAO,
    StockMovementType.CANCELAMENTO,
    StockMovementType.COMPRA,
}
OUTBOUND_MOVEMENTS = {
    StockMovementType.SAIDA,
    StockMovementType.VENDA,
    StockMovementType.PERDA,
}
TARGET_MOVEMENTS = {StockMovementType.AJUSTE, StockMovementType.INVENTARIO}


def apply_stock_movement(
    db: Session,
    *,
    product: Product,
    user: User,
    movement_type: StockMovementType,
    quantity: float,
    reason: str | None = None,
    target_stock: float | None = None,
    reference_type: str | None = None,
    reference_id: int | None = None,
    allow_negative: bool = False,
) -> StockMovement:
    previous_stock = round(float(product.stock_quantity), 2)
    quantity = round(float(quantity), 2)
    if quantity <= 0:
        raise StockValidationError("A quantidade da movimentação deve ser maior que zero.")
    if product.unit == ProductUnit.UN.value and not quantity.is_integer():
        raise StockValidationError("Produtos por unidade devem ser movimentados em quantidades inteiras.")

    if movement_type in INBOUND_MOVEMENTS:
        new_stock = previous_stock + quantity
    elif movement_type in OUTBOUND_MOVEMENTS:
        if previous_stock < quantity and not allow_negative:
            raise StockValidationError(f"Estoque insuficiente para {product.name}.")
        new_stock = previous_stock - quantity
    elif movement_type in TARGET_MOVEMENTS:
        if target_stock is None or target_stock < 0:
            raise StockValidationError("Informe o estoque final para ajuste ou inventário.")
        new_stock = round(float(target_stock), 2)
        if product.unit == ProductUnit.UN.value and not new_stock.is_integer():
            raise StockValidationError("Produtos por unidade devem usar estoque em números inteiros.")
        quantity = abs(new_stock - previous_stock)
        if quantity == 0:
            raise StockValidationError("O estoque informado é igual ao estoque atual.")
    else:
        raise StockValidationError("Tipo de movimentação não suportado.")

    product.stock_quantity = round(new_stock, 2)
    movement = StockMovement(
        account_id=product.account_id,
        product_id=product.id,
        user_id=user.id,
        type=movement_type,
        quantity=quantity,
        previous_stock=previous_stock,
        new_stock=product.stock_quantity,
        reason=reason,
        reference_type=reference_type,
        reference_id=reference_id,
    )
    db.add(movement)
    return movement


def product_status(stock_quantity: float, minimum_stock: float) -> str:
    if stock_quantity <= 0:
        return "SEM ESTOQUE"
    if stock_quantity <= minimum_stock * 0.5:
        return "CRÍTICO"
    if stock_quantity <= minimum_stock:
        return "BAIXO"
    return "NORMAL"


def average_sales_last_30_days(db: Session, account_id: int, product_id: int) -> float:
    since = datetime.utcnow() - timedelta(days=30)
    total_quantity = (
        db.query(func.coalesce(func.sum(SaleItem.quantity), 0))
        .join(Sale, Sale.id == SaleItem.sale_id)
        .filter(
            Sale.account_id == account_id,
            SaleItem.product_id == product_id,
            Sale.created_at >= since,
            Sale.status == SaleStatus.COMPLETED,
        )
        .scalar()
    )
    return round(float(total_quantity or 0) / 30, 2)


def inventory_projection(db: Session, product: Product, account_id: int) -> dict:
    avg_per_day = average_sales_last_30_days(db, account_id, product.id)
    current_stock = float(product.stock_quantity)
    minimum_stock = float(product.minimum_stock)
    days_remaining = round(current_stock / avg_per_day, 1) if avg_per_day > 0 else None
    recommended_stock = avg_per_day * 15
    purchase_recommendation = max(round(recommended_stock - current_stock, 2), 0)

    return {
        "average_sales_per_day": avg_per_day,
        "days_remaining": days_remaining,
        "purchase_recommendation": purchase_recommendation,
        "status": product_status(current_stock, minimum_stock),
    }
