import os
from pathlib import Path

from fastapi.testclient import TestClient

os.environ["DATABASE_URL"] = "sqlite:///./test_marketpulse.db"

db_path = Path("test_marketpulse.db")
if db_path.exists():
    db_path.unlink()

from app.main import app  # noqa: E402


def run():
    with TestClient(app) as client:
        login = client.post(
            "/auth/login",
            json={"email": "admin@marketpulse.dev", "password": "admin123"},
        )
        assert login.status_code == 200, login.text
        token = login.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        products = client.get("/products", headers=headers)
        assert products.status_code == 200, products.text
        all_products = products.json()
        product = next(item for item in all_products if item["stock_quantity"] >= 2 and item["barcode"])
        initial_stock = product["stock_quantity"]

        lookup = client.get(f"/products/barcode/{product['barcode']}", headers=headers)
        assert lookup.status_code == 200, lookup.text

        sale = client.post(
            "/sales",
            headers=headers,
            json={
                "items": [{"product_id": product["id"], "quantity": 2, "discount": 0}],
                "discount": 0,
                "payment_method": "PIX",
            },
        )
        assert sale.status_code == 201, sale.text
        sale_id = sale.json()["id"]

        inventory = client.get("/inventory", headers=headers)
        assert inventory.status_code == 200, inventory.text
        updated_product = next(item for item in inventory.json() if item["product_id"] == product["id"])

        movements = client.get("/inventory/movements", headers=headers)
        assert movements.status_code == 200, movements.text
        movement_found = any(item["reason"] == f"Venda #{sale_id}" for item in movements.json())

        dashboard = client.get("/dashboard/summary", headers=headers)
        assert dashboard.status_code == 200, dashboard.text

        sales = client.get("/sales", headers=headers)
        assert sales.status_code == 200, sales.text

        print(
            {
                "product": product["name"],
                "initial_stock": initial_stock,
                "final_stock": updated_product["stock_quantity"],
                "sale_id": sale_id,
                "movement_found": movement_found,
                "sales_count": len(sales.json()),
                "dashboard_sales_today": dashboard.json()["sales_today"]["value"],
            }
        )


if __name__ == "__main__":
    run()
