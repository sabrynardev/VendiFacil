from datetime import datetime, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.product import Product
from app.models.sale import Sale, SaleItem, SaleStatus


def product_status(stock_quantity: float, minimum_stock: float) -> str:
    if stock_quantity <= 0:
        return "SEM ESTOQUE"
    if stock_quantity <= minimum_stock * 0.5:
        return "CRÍTICO"
    if stock_quantity <= minimum_stock:
        return "BAIXO"
    return "NORMAL"


def average_sales_last_30_days(db: Session, product_id: int) -> float:
    since = datetime.utcnow() - timedelta(days=30)
    total_quantity = (
        db.query(func.coalesce(func.sum(SaleItem.quantity), 0))
        .join(Sale, Sale.id == SaleItem.sale_id)
        .filter(SaleItem.product_id == product_id, Sale.created_at >= since, Sale.status == SaleStatus.COMPLETED)
        .scalar()
    )
    return round(float(total_quantity or 0) / 30, 2)


def inventory_projection(db: Session, product: Product) -> dict:
    avg_per_day = average_sales_last_30_days(db, product.id)
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
