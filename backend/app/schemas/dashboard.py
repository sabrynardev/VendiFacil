from pydantic import BaseModel


class SummaryCard(BaseModel):
    value: float
    delta: float


class DashboardSummary(BaseModel):
    revenue_today: SummaryCard
    sales_today: SummaryCard
    average_ticket: SummaryCard
    low_stock_products: int


class RevenuePoint(BaseModel):
    day: str
    revenue: float


class CategorySalesPoint(BaseModel):
    category: str
    sales: float


class PaymentMethodPoint(BaseModel):
    method: str
    total: float


class TopProductPoint(BaseModel):
    product: str
    quantity: float
