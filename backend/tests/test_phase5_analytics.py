from datetime import date, datetime, timedelta

from app.database.session import SessionLocal
from app.models.customer import CustomerDebt
from app.models.product import Product


def create_product(client, headers, name, sku, sale_price, cost_price, stock=20):
    category = client.get("/categories", headers=headers).json()[0]
    response = client.post("/products", headers=headers, json={"name": name, "sku": sku, "category_id": category["id"], "cost_price": cost_price, "sale_price": sale_price, "stock_quantity": stock, "minimum_stock": 1, "unit": "UN", "active": True})
    assert response.status_code == 201, response.text
    return response.json()


def sell(client, headers, product, *, quantity=1, payments=None, key=None):
    total = round(product["sale_price"] * quantity, 2)
    response = client.post("/sales", headers=headers, json={"items": [{"product_id": product["id"], "quantity": quantity}], "payments": payments or [{"method": "PIX", "amount": total}], "idempotency_key": key or f"analytics-{product['id']}-{quantity}"})
    assert response.status_code == 201, response.text
    return response.json()


def overview(client, headers, stopped_days=30):
    today = date.today().isoformat()
    response = client.get(f"/analytics/overview?start={today}&end={today}&stopped_days={stopped_days}", headers=headers)
    assert response.status_code == 200, response.text
    return response.json()


def test_abc_order_percentages_classes_and_empty_period(client, auth_headers):
    a = create_product(client, auth_headers, "Produto A", "ABC-A", 80, 40)
    b = create_product(client, auth_headers, "Produto B", "ABC-B", 15, 5)
    c = create_product(client, auth_headers, "Produto C", "ABC-C", 5, 2)
    sell(client, auth_headers, a); sell(client, auth_headers, b); sell(client, auth_headers, c)
    rows = overview(client, auth_headers)["products"]["abc"]
    assert [item["product"] for item in rows] == ["Produto A", "Produto B", "Produto C"]
    assert [item["percentage"] for item in rows] == [80, 15, 5]
    assert [item["cumulative_percentage"] for item in rows] == [80, 95, 100]
    assert [item["class"] for item in rows] == ["A", "B", "C"]
    old_start = (date.today() - timedelta(days=400)).isoformat(); old_end = (date.today() - timedelta(days=399)).isoformat()
    empty = client.get(f"/analytics/overview?start={old_start}&end={old_end}", headers=auth_headers).json()
    assert empty["products"]["abc"] == []


def test_dashboard_margin_snapshot_cancel_and_mixed_payment(client, auth_headers):
    first = create_product(client, auth_headers, "Venda 100", "DASH-100", 100, 60)
    second = create_product(client, auth_headers, "Venda 200", "DASH-200", 200, 120)
    cancelled_product = create_product(client, auth_headers, "Cancelada", "DASH-CANCEL", 100, 10)
    sell(client, auth_headers, first, payments=[{"method": "PIX", "amount": 40}, {"method": "DINHEIRO", "amount": 60, "amount_received": 60}], key="mixed-report")
    sell(client, auth_headers, second)
    cancelled = sell(client, auth_headers, cancelled_product)
    assert client.post(f"/sales/{cancelled['id']}/cancel", headers=auth_headers, json={"reason": "Teste analytics"}).status_code == 200
    changed = {key: first.get(key) for key in ["name", "brand", "description", "sku", "barcode", "category_id", "supplier_id", "sale_price", "stock_quantity", "minimum_stock", "unit", "active"]}; changed["cost_price"] = 999
    assert client.put(f"/products/{first['id']}", headers=auth_headers, json=changed).status_code == 200
    data = overview(client, auth_headers)
    assert data["summary"]["revenue"] == 300
    assert data["summary"]["cmv"] == 180
    assert data["summary"]["gross_profit"] == 120
    methods = {item["method"]: item["amount"] for item in data["sales"]["payment_methods"]}
    assert methods["PIX"] == 240
    assert methods["DINHEIRO"] == 60
    first_row = next(item for item in data["products"]["products"] if item["product_id"] == first["id"])
    assert first_row["cmv"] == 60
    assert first_row["profit"] == 40


def test_stopped_products_excludes_recent_and_zero_stock(client, auth_headers):
    stopped = create_product(client, auth_headers, "Produto parado", "STOP-OLD", 10, 4, stock=10)
    recent = create_product(client, auth_headers, "Produto recente", "STOP-RECENT", 10, 4, stock=10)
    zero = create_product(client, auth_headers, "Produto zerado", "STOP-ZERO", 10, 4, stock=0)
    sell(client, auth_headers, recent, key="recent-sale")
    with SessionLocal() as db:
        old = datetime.utcnow() - timedelta(days=45)
        db.query(Product).filter(Product.id.in_([stopped["id"], zero["id"]])).update({Product.created_at: old}, synchronize_session=False)
        db.commit()
    rows = overview(client, auth_headers, stopped_days=30)["products"]["stopped"]
    ids = {item["product_id"] for item in rows}
    assert stopped["id"] in ids
    assert recent["id"] not in ids
    assert zero["id"] not in ids
    stopped_row = next(item for item in rows if item["product_id"] == stopped["id"])
    assert stopped_row["stopped_value"] == 40


def test_credit_aging_partial_payment_and_paid_debt_exclusion(client, auth_headers):
    product = create_product(client, auth_headers, "Fiado analytics", "CREDIT-AN", 100, 40, stock=5)
    customer = client.post("/customers", headers=auth_headers, json={"name":"Cliente Analytics","credit_limit":500,"credit_blocked":False,"active":True}).json()
    sale = client.post("/sales", headers=auth_headers, json={"items":[{"product_id":product["id"],"quantity":1}],"payments":[{"method":"FIADO","amount":100}],"customer_id":customer["id"],"credit_due_date":(date.today()-timedelta(days=10)).isoformat(),"idempotency_key":"credit-analytics"})
    assert sale.status_code == 201
    assert client.post(f"/customers/{customer['id']}/payments", headers=auth_headers, json={"amount":30,"method":"PIX"}).status_code == 201
    credit = overview(client, auth_headers)["credit"]
    assert credit["open_total"] == 70
    assert credit["overdue_total"] == 70
    assert credit["debtor_count"] == 1
    assert next(item for item in credit["aging_buckets"] if item["bucket"] == "8_30_DIAS")["amount"] == 70
    assert client.post(f"/customers/{customer['id']}/payments", headers=auth_headers, json={"amount":70,"method":"PIX"}).status_code == 201
    assert overview(client, auth_headers)["credit"]["open_total"] == 0


def test_losses_suppliers_and_csv_export(client, auth_headers):
    product = create_product(client, auth_headers, "Perda e compra", "LOSS-SUP", 12, 5, stock=20)
    loss = client.post("/management-inventory/losses", headers=auth_headers, json={"product_id":product["id"],"quantity":2,"reason":"DANIFICADO"})
    assert loss.status_code == 201, loss.text
    suppliers = client.get("/suppliers", headers=auth_headers).json()[:2]
    for index, supplier in enumerate(suppliers):
        order = client.post("/purchases", headers=auth_headers, json={"supplier_id":supplier["id"],"items":[{"product_id":product["id"],"quantity":2,"unit_cost":6+index}]}).json()
        item = order["items"][0]
        assert client.post(f"/purchases/{order['id']}/receive", headers=auth_headers, json={"items":[{"order_item_id":item["id"],"quantity":2,"unit_cost":6+index}]}).status_code == 200
    data = overview(client, auth_headers)
    assert data["losses"]["total_value"] == 10
    assert next(item for item in data["losses"]["by_reason"] if item["reason"] == "DANIFICADO")["value"] == 10
    assert len(data["suppliers"]["ranking"]) == 2
    assert any(item["product"] == "Perda e compra" for item in data["suppliers"]["comparisons"])
    today=date.today().isoformat(); exported=client.get(f"/analytics/export?report=abc&start={today}&end={today}",headers=auth_headers)
    assert exported.status_code == 200
    assert "Produto;Faturamento" in exported.json()["content"]
    assert exported.json()["filename"] == "vendi-abc.csv"
