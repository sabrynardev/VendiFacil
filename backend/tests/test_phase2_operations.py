from decimal import Decimal, ROUND_HALF_UP


def sale_payload(product, *, payments=None, quantity=1):
    total = float((Decimal(str(product["sale_price"])) * Decimal(str(quantity))).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))
    return {
        "items": [{"product_id": product["id"], "quantity": quantity, "discount": 0}],
        "discount": 0,
        "surcharge": 0,
        "payments": payments or [{"method": "PIX", "amount": total}],
        "idempotency_key": f"test-sale-{product['id']}-{quantity}",
    }


def test_sale_requires_open_cash_register(client):
    login = client.post("/auth/login", json={"email": "admin@marketpulse.dev", "password": "admin123"})
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    product = next(item for item in client.get("/products", headers=headers).json() if item["stock_quantity"] >= 1)
    response = client.post("/sales", headers=headers, json=sale_payload(product))
    assert response.status_code == 400
    assert "Abra o caixa" in response.json()["detail"]


def test_cash_register_open_supply_withdrawal_and_close(client, auth_headers):
    duplicate = client.post("/cash-registers/open", headers=auth_headers, json={"opening_balance": 50})
    assert duplicate.status_code == 400

    assert client.post("/cash-registers/supply", headers=auth_headers, json={"amount": 20, "reason": "Troco adicional"}).status_code == 200
    assert client.post("/cash-registers/withdrawal", headers=auth_headers, json={"amount": 10, "reason": "Retirada para cofre"}).status_code == 200
    current = client.get("/cash-registers/current", headers=auth_headers).json()
    assert current["summary"]["expected_cash"] == 110
    excessive = client.post("/cash-registers/withdrawal", headers=auth_headers, json={"amount": 111, "reason": "Valor inválido"})
    assert excessive.status_code == 400

    closed = client.post("/cash-registers/close", headers=auth_headers, json={"counted_balance": 108, "note": "Contagem final"})
    assert closed.status_code == 200
    assert closed.json()["difference"] == -2
    assert client.get("/cash-registers/current", headers=auth_headers).json() is None


def test_mixed_payment_calculates_cash_change_and_register_summary(client, auth_headers):
    product = next(item for item in client.get("/products", headers=auth_headers).json() if item["stock_quantity"] >= 1)
    total = product["sale_price"]
    cash_part = round(total / 2, 2)
    pix_part = round(total - cash_part, 2)
    payload = sale_payload(product, payments=[
        {"method": "PIX", "amount": pix_part},
        {"method": "DINHEIRO", "amount": cash_part, "amount_received": cash_part + 10},
    ])
    response = client.post("/sales", headers=auth_headers, json=payload)
    assert response.status_code == 201, response.text
    assert response.json()["change_amount"] == 10
    assert len(response.json()["payments"]) == 2
    summary = client.get("/cash-registers/current", headers=auth_headers).json()["summary"]
    assert summary["cash_sales"] == cash_part
    assert summary["pix_sales"] == pix_part


def test_mixed_payment_rejects_wrong_sum(client, auth_headers):
    product = next(item for item in client.get("/products", headers=auth_headers).json() if item["stock_quantity"] >= 1)
    payload = sale_payload(product, payments=[{"method": "PIX", "amount": 1}])
    response = client.post("/sales", headers=auth_headers, json=payload)
    assert response.status_code == 400
    assert "soma dos pagamentos" in response.json()["detail"]


def test_hold_sale_does_not_change_stock_and_can_be_completed(client, auth_headers):
    product = next(item for item in client.get("/products", headers=auth_headers).json() if item["stock_quantity"] >= 2)
    initial = product["stock_quantity"]
    held = client.post("/sales/hold", headers=auth_headers, json={
        "items": [{"product_id": product["id"], "quantity": 2, "discount": 0}], "discount": 0, "surcharge": 0, "note": "Cliente voltou"
    })
    assert held.status_code == 201, held.text
    assert held.json()["status"] == "ON_HOLD"
    unchanged = next(item for item in client.get("/products", headers=auth_headers).json() if item["id"] == product["id"])
    assert unchanged["stock_quantity"] == initial

    completed = client.post(f"/sales/{held.json()['id']}/complete", headers=auth_headers, json=sale_payload(product, quantity=2))
    assert completed.status_code == 200, completed.text
    assert completed.json()["status"] == "COMPLETED"
    updated = next(item for item in client.get("/products", headers=auth_headers).json() if item["id"] == product["id"])
    assert updated["stock_quantity"] == initial - 2


def test_cancel_sale_restores_stock_cash_and_audit(client, auth_headers):
    product = next(item for item in client.get("/products", headers=auth_headers).json() if item["stock_quantity"] >= 1)
    initial = product["stock_quantity"]
    created = client.post("/sales", headers=auth_headers, json=sale_payload(product))
    assert created.status_code == 201
    cancelled = client.post(f"/sales/{created.json()['id']}/cancel", headers=auth_headers, json={"reason": "Cliente desistiu"})
    assert cancelled.status_code == 200, cancelled.text
    assert cancelled.json()["status"] == "CANCELLED"
    restored = next(item for item in client.get("/products", headers=auth_headers).json() if item["id"] == product["id"])
    assert restored["stock_quantity"] == initial
    movements = client.get("/inventory/movements", headers=auth_headers).json()
    assert any(item["type"] == "cancelamento" and item["reference_id"] == created.json()["id"] for item in movements)
    assert client.post(f"/sales/{created.json()['id']}/cancel", headers=auth_headers, json={"reason": "Duplicado"}).status_code == 400
    audit = client.get("/audit", headers=auth_headers).json()
    assert any(item["action"] == "CANCEL" and item["entity_id"] == str(created.json()["id"]) for item in audit)
    summary = client.get("/cash-registers/current", headers=auth_headers).json()["summary"]
    assert summary["total_sales"] == 0
    assert summary["pix_sales"] == 0


def test_cashier_can_cancel_own_hold_but_not_completed_sale(client):
    admin_login = client.post("/auth/login", json={"email": "admin@marketpulse.dev", "password": "admin123"}).json()
    admin_headers = {"Authorization": f"Bearer {admin_login['access_token']}"}
    product = next(item for item in client.get("/products", headers=admin_headers).json() if item["stock_quantity"] >= 1)

    login = client.post("/auth/login", json={"email": "sabrina@marketpulse.dev", "password": "caixa123"})
    headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
    assert client.post("/cash-registers/open", headers=headers, json={"opening_balance": 50}).status_code == 201
    hold = client.post("/sales/hold", headers=headers, json={
        "items": [{"product_id": product["id"], "quantity": 1, "discount": 0}], "discount": 0, "surcharge": 0
    })
    assert client.post(f"/sales/{hold.json()['id']}/cancel", headers=headers, json={"reason": "Cliente desistiu"}).status_code == 200

    completed = client.post("/sales", headers=headers, json=sale_payload(product))
    assert completed.status_code == 201, completed.text
    denied = client.post(f"/sales/{completed.json()['id']}/cancel", headers=headers, json={"reason": "Sem autorização"})
    assert denied.status_code == 403


def test_special_discount_requires_and_accepts_manager_authorization(client):
    admin_login = client.post("/auth/login", json={"email": "admin@marketpulse.dev", "password": "admin123"}).json()
    admin_headers = {"Authorization": f"Bearer {admin_login['access_token']}"}
    product = next(item for item in client.get("/products", headers=admin_headers).json() if item["stock_quantity"] >= 1 and item["sale_price"] > 1)
    cashier_login = client.post("/auth/login", json={"email": "sabrina@marketpulse.dev", "password": "caixa123"}).json()
    headers = {"Authorization": f"Bearer {cashier_login['access_token']}"}
    client.post("/cash-registers/open", headers=headers, json={"opening_balance": 50})

    discount = round(product["sale_price"] * 0.2, 2)
    total = round(product["sale_price"] - discount, 2)
    payload = {
        "items": [{"product_id": product["id"], "quantity": 1, "discount": 0}],
        "discount": discount,
        "payments": [{"method": "PIX", "amount": total}],
        "idempotency_key": "special-discount-without-auth",
    }
    denied = client.post("/sales", headers=headers, json=payload)
    assert denied.status_code == 400
    assert "autorização" in denied.json()["detail"]

    payload.update({
        "idempotency_key": "special-discount-authorized",
        "authorization_email": "admin@marketpulse.dev",
        "authorization_password": "admin123",
    })
    approved = client.post("/sales", headers=headers, json=payload)
    assert approved.status_code == 201, approved.text
    audit = client.get("/audit", headers=admin_headers).json()
    assert any(item["action"] == "SPECIAL_DISCOUNT" and item["entity_id"] == str(approved.json()["id"]) for item in audit)


def test_weight_product_accepts_decimal_quantity(client, auth_headers):
    category = client.get("/categories", headers=auth_headers).json()[0]
    product = client.post("/products", headers=auth_headers, json={"name":"Queijo por kg","sku":"QUEIJO-KG","category_id":category["id"],"cost_price":20,"sale_price":39.9,"stock_quantity":5,"minimum_stock":1,"unit":"KG","active":True}).json()
    payload = sale_payload(product, quantity=0.35)
    response = client.post("/sales", headers=auth_headers, json=payload)
    assert response.status_code == 201, response.text
    assert response.json()["total"] == 13.97
