from fastapi import APIRouter

from app.api.routes import accounts, analytics, audit, auth, cash_registers, categories, customers, dashboard, financial, inventory, management_inventory, products, profiles, purchases, reports, sales, suppliers, users

api_router = APIRouter()
api_router.include_router(accounts.router, prefix="/accounts", tags=["accounts"])
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(profiles.router, prefix="/profiles", tags=["profiles"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(audit.router, prefix="/audit", tags=["audit"])
api_router.include_router(categories.router, prefix="/categories", tags=["categories"])
api_router.include_router(products.router, prefix="/products", tags=["products"])
api_router.include_router(sales.router, prefix="/sales", tags=["sales"])
api_router.include_router(cash_registers.router, prefix="/cash-registers", tags=["cash-registers"])
api_router.include_router(inventory.router, prefix="/inventory", tags=["inventory"])
api_router.include_router(suppliers.router, prefix="/suppliers", tags=["suppliers"])
api_router.include_router(purchases.router, prefix="/purchases", tags=["purchases"])
api_router.include_router(management_inventory.router, prefix="/management-inventory", tags=["management-inventory"])
api_router.include_router(customers.router, prefix="/customers", tags=["customers"])
api_router.include_router(financial.router, prefix="/financial", tags=["financial"])
api_router.include_router(analytics.router, prefix="/analytics", tags=["analytics"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(reports.router, prefix="/reports", tags=["reports"])
