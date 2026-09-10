from datetime import timedelta

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.auth.dependencies import require_permission
from app.core.datetime import local_period_to_utc_bounds, local_today
from app.core.permissions import PermissionCode
from app.database.session import get_db
from app.models.sale import Sale, SaleItem, SaleStatus
from app.models.user import User
from app.services.financial import financial_summary

router = APIRouter()


@router.get("")
def reports(
    period: str = Query(default="7d"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_permission(PermissionCode.REPORTS_VIEW)),
):
    period_map = {"today": 1, "7d": 7, "30d": 30}
    days = period_map.get(period, 7)
    end = local_today()
    start = end - timedelta(days=days - 1)
    start_at, end_at = local_period_to_utc_bounds(start, end)
    summary = financial_summary(db, current_user.account_id, start, end)
    items_sold = float(
        db.query(func.coalesce(func.sum(SaleItem.quantity), 0))
        .join(Sale)
        .filter(
            Sale.account_id == current_user.account_id,
            Sale.status == SaleStatus.COMPLETED,
            Sale.created_at.between(start_at, end_at),
        )
        .scalar()
        or 0
    )

    return {
        "period": period,
        "revenue": summary["revenue"],
        "sales_count": summary["sales_count"],
        "average_ticket": summary["average_ticket"],
        "estimated_profit": summary["gross_profit"],
        "items_sold": items_sold,
    }
