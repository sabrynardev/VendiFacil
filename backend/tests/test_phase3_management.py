from datetime import date, timedelta


def first_product(client, headers, minimum_stock=5):
    return next(item for item in client.get("/products", headers=headers).json() if item["stock_quantity"] >= minimum_stock)


def create_customer(client, headers, **overrides):
    payload = {"name": "Maria da Silva", "phone": "75999990000", "credit_limit": 200, "credit_blocked": False, "active": True}
    payload.update(overrides)
    response = client.post("/customers", headers=headers, json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def credit_sale_payload(product, customer_id, *, amount=None, due_date=None, key="phase3-credit-sale"):
    total = amount if amount is not None else product["sale_price"]
    return {
        "items": [{"product_id": product["id"], "quantity": 1, "discount": 0}],
        "discount": round(product["sale_price"] - total, 2) if total < product["sale_price"] else 0,
        "payments": [{"method": "FIADO", "amount": total}],
        "customer_id": customer_id,
        "credit_due_date": due_date,
        "idempotency_key": key,
    }


def test_purchase_partial_and_complete_receipt_updates_stock_price_and_lot(client, auth_headers):
    product = first_product(client, auth_headers)
    supplier = client.get("/suppliers", headers=auth_headers).json()[0]
    initial = product["stock_quantity"]
    order = client.post("/purchases", headers=auth_headers, json={
        "supplier_id": supplier["id"], "discount": 2,
        "items": [{"product_id": product["id"], "quantity": 10, "unit_cost": 4.5}],
    })
    assert order.status_code == 201, order.text
    assert order.json()["total"] == 43
    item_id = order.json()["items"][0]["id"]

    partial = client.post(f"/purchases/{order.json()['id']}/receive", headers=auth_headers, json={"items": [{
        "order_item_id": item_id, "quantity": 6, "unit_cost": 4.8, "lot_code": "L-001", "expiration_date": (date.today()+timedelta(days=3)).isoformat()
    }]})
    assert partial.status_code == 200, partial.text
    assert partial.json()["status"] == "PARCIALMENTE_RECEBIDO"
    assert partial.json()["items"][0]["pending_quantity"] == 4
    updated = next(item for item in client.get("/products", headers=auth_headers).json() if item["id"] == product["id"])
    assert updated["stock_quantity"] == initial + 6
    lots = client.get("/management-inventory/lots", headers=auth_headers).json()
    assert any(lot["lot_code"] == "L-001" and lot["expiry_state"] == "ATE_3_DIAS" for lot in lots)
    prices = client.get(f"/purchases/history/prices?product_id={product['id']}", headers=auth_headers).json()
    assert prices[0]["unit_cost"] == 4.8

    completed = client.post(f"/purchases/{order.json()['id']}/receive", headers=auth_headers, json={"items": [{"order_item_id": item_id, "quantity": 4, "unit_cost": 5}]})
    assert completed.status_code == 200, completed.text
    assert completed.json()["status"] == "RECEBIDO"
    prices = client.get(f"/purchases/history/prices?product_id={product['id']}", headers=auth_headers).json()
    assert prices[0]["variation_percent"] == 4.17


def test_purchase_rejects_receipt_above_pending_and_links_preferred_supplier(client, auth_headers):
    product = first_product(client, auth_headers)
    supplier = client.get("/suppliers", headers=auth_headers).json()[0]
    link = client.post(f"/purchases/suppliers/{supplier['id']}/products", headers=auth_headers, json={"product_id": product["id"], "preferred": True, "supplier_code": "FORN-10", "lead_time_days": 3})
    assert link.status_code == 200, link.text
    assert link.json()["preferred"] is True
    order = client.post("/purchases", headers=auth_headers, json={"supplier_id": supplier["id"], "items": [{"product_id": product["id"], "quantity": 2, "unit_cost": 4}]})
    item_id = order.json()["items"][0]["id"]
    invalid = client.post(f"/purchases/{order.json()['id']}/receive", headers=auth_headers, json={"items": [{"order_item_id": item_id, "quantity": 3}]})
    assert invalid.status_code == 400
    assert "supera" in invalid.json()["detail"]


def test_expired_lot_loss_reduces_lot_and_stock(client, auth_headers):
    product = first_product(client, auth_headers)
    initial = product["stock_quantity"]
    lot = client.post("/management-inventory/lots", headers=auth_headers, json={
        "product_id": product["id"], "lot_code": "VENC-01", "quantity": 5, "unit_cost": 3, "expiration_date": (date.today()-timedelta(days=1)).isoformat()
    })
    assert lot.status_code == 201, lot.text
    assert lot.json()["expiry_state"] == "VENCIDO"
    loss = client.post("/management-inventory/losses", headers=auth_headers, json={"product_id": product["id"], "lot_id": lot.json()["id"], "quantity": 2, "reason": "VENCIDO", "notes": "Baixa de validade"})
    assert loss.status_code == 201, loss.text
    lots = client.get(f"/management-inventory/lots?product_id={product['id']}", headers=auth_headers).json()
    assert lots[0]["current_quantity"] == 3
    updated = next(item for item in client.get("/products", headers=auth_headers).json() if item["id"] == product["id"])
    assert updated["stock_quantity"] == initial + 3
    movements = client.get("/inventory/movements", headers=auth_headers).json()
    assert any(item["type"] == "perda" and item["reference_type"] == "inventory_loss" for item in movements)


def test_inventory_positive_negative_and_cancelled_count(client, auth_headers):
    products = client.get("/products", headers=auth_headers).json()[:2]
    inventory = client.post("/management-inventory/counts", headers=auth_headers, json={"product_ids": [item["id"] for item in products], "notes": "Contagem bebidas"})
    assert inventory.status_code == 201, inventory.text
    values = [
        {"product_id": products[0]["id"], "counted_quantity": products[0]["stock_quantity"] + 2},
        {"product_id": products[1]["id"], "counted_quantity": max(products[1]["stock_quantity"] - 1, 0)},
    ]
    completed = client.post(f"/management-inventory/counts/{inventory.json()['id']}/complete", headers=auth_headers, json={"items": values})
    assert completed.status_code == 200, completed.text
    assert completed.json()["status"] == "CONCLUIDO"
    assert completed.json()["positive_differences"] == 2
    assert completed.json()["negative_differences"] == -1

    cancelled = client.post("/management-inventory/counts", headers=auth_headers, json={"product_ids": [products[0]["id"]]})
    stock_before = next(item for item in client.get("/products", headers=auth_headers).json() if item["id"] == products[0]["id"])["stock_quantity"]
    response = client.post(f"/management-inventory/counts/{cancelled.json()['id']}/cancel", headers=auth_headers)
    assert response.json()["status"] == "CANCELADO"
    stock_after = next(item for item in client.get("/products", headers=auth_headers).json() if item["id"] == products[0]["id"])["stock_quantity"]
    assert stock_after == stock_before


def test_credit_sale_requires_customer_and_supports_partial_and_full_payment(client, auth_headers):
    product = first_product(client, auth_headers, 3)
    without_customer = credit_sale_payload(product, None, key="credit-no-customer")
    response = client.post("/sales", headers=auth_headers, json=without_customer)
    assert response.status_code == 400
    assert "cliente" in response.json()["detail"].lower()

    customer = create_customer(client, auth_headers)
    first = client.post("/sales", headers=auth_headers, json=credit_sale_payload(product, customer["id"], key="credit-first"))
    second = client.post("/sales", headers=auth_headers, json=credit_sale_payload(product, customer["id"], key="credit-second"))
    assert first.status_code == second.status_code == 201
    balance = round(product["sale_price"] * 2, 2)
    detail = client.get(f"/customers/{customer['id']}", headers=auth_headers).json()
    assert detail["balance"] == balance

    partial_amount = round(product["sale_price"] + 1, 2)
    partial = client.post(f"/customers/{customer['id']}/payments", headers=auth_headers, json={"amount": partial_amount, "method": "DINHEIRO", "notes": "Pagamento parcial"})
    assert partial.status_code == 201, partial.text
    assert partial.json()["balance_after"] == round(balance - partial_amount, 2)
    detail = client.get(f"/customers/{customer['id']}", headers=auth_headers).json()
    assert detail["debts"][0]["status"] == "QUITADO"
    assert detail["debts"][1]["status"] == "PARCIAL"
    final = client.post(f"/customers/{customer['id']}/payments", headers=auth_headers, json={"amount": detail["balance"], "method": "PIX"})
    assert final.status_code == 201
    assert final.json()["balance_after"] == 0


def test_credit_limit_overdue_block_and_cancel_reverses_debt(client, auth_headers):
    product = first_product(client, auth_headers, 2)
    customer = create_customer(client, auth_headers, credit_limit=max(product["sale_price"] - 1, 0))

    cashier_login = client.post("/auth/login", json={"email": "sabrina@marketpulse.dev", "password": "caixa123"}).json()
    cashier_headers = {"Authorization": f"Bearer {cashier_login['access_token']}"}
    client.post("/cash-registers/open", headers=cashier_headers, json={"opening_balance": 50})
    payload = credit_sale_payload(product, customer["id"], due_date=(date.today()-timedelta(days=1)).isoformat(), key="limit-denied")
    denied = client.post("/sales", headers=cashier_headers, json=payload)
    assert denied.status_code == 400
    assert "limite" in denied.json()["detail"].lower()
    payload.update({"idempotency_key": "limit-authorized", "authorization_email": "admin@marketpulse.dev", "authorization_password": "admin123"})
    approved = client.post("/sales", headers=cashier_headers, json=payload)
    assert approved.status_code == 201, approved.text
    detail = client.get(f"/customers/{customer['id']}", headers=auth_headers).json()
    assert detail["overdue_balance"] == product["sale_price"]
    assert detail["debts"][0]["is_overdue"] is True

    cancelled = client.post(f"/sales/{approved.json()['id']}/cancel", headers=auth_headers, json={"reason": "Venda fiada cancelada"})
    assert cancelled.status_code == 200, cancelled.text
    detail = client.get(f"/customers/{customer['id']}", headers=auth_headers).json()
    assert detail["balance"] == 0
    assert detail["debts"][0]["status"] == "ESTORNADO"

    blocked = create_customer(client, auth_headers, name="Cliente bloqueado", credit_blocked=True)
    blocked_sale = client.post("/sales", headers=auth_headers, json=credit_sale_payload(product, blocked["id"], key="blocked-credit"))
    assert blocked_sale.status_code == 400
    assert "bloqueado" in blocked_sale.json()["detail"].lower()
