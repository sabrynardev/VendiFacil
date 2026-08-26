from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database.session import get_db
from app.models.product import Product
from app.models.sale import Sale, SaleItem, SaleStatus

router = APIRouter()


@router.get("")
def reports(
    period: str = Query(default="7d"),
    db: Session = Depends(get_db),
    _: object = Depends(get_current_user),
):
    period_map = {"today": 1, "7d": 7, "30d": 30}
    days = period_map.get(period, 7)
    since = datetime.utcnow() - timedelta(days=days)

    revenue = float(
        db.query(func.coalesce(func.sum(Sale.total), 0))
        .filter(Sale.created_at >= since, Sale.status == SaleStatus.COMPLETED)
        .scalar()
        or 0
    )
    sales_count = int(
        db.query(func.count(Sale.id))
        .filter(Sale.created_at >= since, Sale.status == SaleStatus.COMPLETED)
        .scalar()
        or 0
    )
    average_ticket = round(revenue / sales_count, 2) if sales_count else 0
    estimated_profit = float(
        db.query(func.coalesce(func.sum((Product.sale_price - Product.cost_price) * SaleItem.quantity), 0))
        .join(SaleItem, SaleItem.product_id == Product.id)
        .join(Sale, Sale.id == SaleItem.sale_id)
        .filter(Sale.created_at >= since, Sale.status == SaleStatus.COMPLETED)
        .scalar()
        or 0
    )
    items_sold = float(
        db.query(func.coalesce(func.sum(SaleItem.quantity), 0))
        .join(Sale, Sale.id == SaleItem.sale_id)
        .filter(Sale.created_at >= since, Sale.status == SaleStatus.COMPLETED)
        .scalar()
        or 0
    )

    return {
        "period": period,
        "revenue": revenue,
        "sales_count": sales_count,
        "average_ticket": average_ticket,
        "estimated_profit": round(estimated_profit, 2),
        "items_sold": items_sold,
    }
