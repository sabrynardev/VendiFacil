from datetime import datetime, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.category import Category
from app.models.product import Product
from app.models.sale import Sale, SaleItem, SaleStatus
from app.services.inventory import product_status


def _day_bounds(offset_days: int = 0):
    target = datetime.utcnow().date() - timedelta(days=offset_days)
    start = datetime.combine(target, datetime.min.time())
    end = datetime.combine(target, datetime.max.time())
    return start, end


def summary(db: Session, account_id: int) -> dict:
    today_start, today_end = _day_bounds(0)
    yesterday_start, yesterday_end = _day_bounds(1)

    revenue_today = float(
        db.query(func.coalesce(func.sum(Sale.total), 0))
        .filter(
            Sale.account_id == account_id,
            Sale.created_at.between(today_start, today_end),
            Sale.status == SaleStatus.COMPLETED,
        )
        .scalar()
        or 0
    )
    revenue_yesterday = float(
        db.query(func.coalesce(func.sum(Sale.total), 0))
        .filter(
            Sale.account_id == account_id,
            Sale.created_at.between(yesterday_start, yesterday_end),
            Sale.status == SaleStatus.COMPLETED,
        )
        .scalar()
        or 0
    )

    sales_today = int(
        db.query(func.count(Sale.id))
        .filter(
            Sale.account_id == account_id,
            Sale.created_at.between(today_start, today_end),
            Sale.status == SaleStatus.COMPLETED,
        )
        .scalar()
        or 0
    )
    sales_yesterday = int(
        db.query(func.count(Sale.id))
        .filter(
            Sale.account_id == account_id,
            Sale.created_at.between(yesterday_start, yesterday_end),
            Sale.status == SaleStatus.COMPLETED,
        )
        .scalar()
        or 0
    )

    average_ticket_today = round(revenue_today / sales_today, 2) if sales_today else 0
    average_ticket_yesterday = round(revenue_yesterday / sales_yesterday, 2) if sales_yesterday else 0

    low_stock_products = 0
    for product in db.query(Product).filter(Product.account_id == account_id).all():
        if product_status(float(product.stock_quantity), float(product.minimum_stock)) in {"BAIXO", "CRÍTICO", "SEM ESTOQUE"}:
            low_stock_products += 1

    return {
        "revenue_today": {"value": revenue_today, "delta": round(revenue_today - revenue_yesterday, 2)},
        "sales_today": {"value": sales_today, "delta": sales_today - sales_yesterday},
        "average_ticket": {"value": average_ticket_today, "delta": round(average_ticket_today - average_ticket_yesterday, 2)},
        "low_stock_products": low_stock_products,
    }


def revenue_last_7_days(db: Session, account_id: int) -> list[dict]:
    points = []
    for offset in range(6, -1, -1):
        start, end = _day_bounds(offset)
        total = float(
            db.query(func.coalesce(func.sum(Sale.total), 0))
            .filter(
                Sale.account_id == account_id,
                Sale.created_at.between(start, end),
                Sale.status == SaleStatus.COMPLETED,
            )
            .scalar()
            or 0
        )
        points.append({"day": start.strftime("%d/%m"), "revenue": total})
    return points


def top_products(db: Session, account_id: int, limit: int = 5) -> list[dict]:
    rows = (
        db.query(Product.name, func.coalesce(func.sum(SaleItem.quantity), 0).label("quantity"))
        .join(SaleItem, SaleItem.product_id == Product.id)
        .join(Sale, Sale.id == SaleItem.sale_id)
        .filter(Product.account_id == account_id, Sale.account_id == account_id, Sale.status == SaleStatus.COMPLETED)
        .group_by(Product.name)
        .order_by(func.sum(SaleItem.quantity).desc())
        .limit(limit)
        .all()
    )
    return [{"product": row[0], "quantity": float(row[1])} for row in rows]


def sales_by_category(db: Session, account_id: int) -> list[dict]:
    rows = (
        db.query(func.coalesce(Category.name, "Sem categoria"), func.coalesce(func.sum(SaleItem.subtotal), 0))
        .join(Product, Product.category_id == Category.id)
        .join(SaleItem, SaleItem.product_id == Product.id)
        .join(Sale, Sale.id == SaleItem.sale_id)
        .filter(Category.account_id == account_id, Product.account_id == account_id, Sale.account_id == account_id, Sale.status == SaleStatus.COMPLETED)
        .group_by(Category.name)
        .all()
    )
    return [{"category": row[0], "sales": float(row[1])} for row in rows]


def payment_methods(db: Session, account_id: int) -> list[dict]:
    rows = (
        db.query(Sale.payment_method, func.coalesce(func.sum(Sale.total), 0))
        .filter(Sale.account_id == account_id, Sale.status == SaleStatus.COMPLETED)
        .group_by(Sale.payment_method)
        .all()
    )
    return [{"method": row[0], "total": float(row[1])} for row in rows]
