from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database.session import get_db
from app.schemas.dashboard import (
    CategorySalesPoint,
    DashboardSummary,
    PaymentMethodPoint,
    RevenuePoint,
    TopProductPoint,
)
from app.services import dashboard as dashboard_service

router = APIRouter()


@router.get("/summary", response_model=DashboardSummary)
def get_summary(db: Session = Depends(get_db), _: object = Depends(get_current_user)):
    return dashboard_service.summary(db)


@router.get("/revenue", response_model=list[RevenuePoint])
def revenue(db: Session = Depends(get_db), _: object = Depends(get_current_user)):
    return dashboard_service.revenue_last_7_days(db)


@router.get("/top-products", response_model=list[TopProductPoint])
def top_products(db: Session = Depends(get_db), _: object = Depends(get_current_user)):
    return dashboard_service.top_products(db)


@router.get("/payment-methods", response_model=list[PaymentMethodPoint])
def payment_methods(db: Session = Depends(get_db), _: object = Depends(get_current_user)):
    return dashboard_service.payment_methods(db)


@router.get("/category-sales", response_model=list[CategorySalesPoint])
def category_sales(db: Session = Depends(get_db), _: object = Depends(get_current_user)):
    return dashboard_service.sales_by_category(db)
