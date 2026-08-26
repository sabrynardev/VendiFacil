def test_sale_updates_stock_and_registers_movement(client, auth_headers):
    products = client.get("/products", headers=auth_headers).json()
    product = next(item for item in products if item["stock_quantity"] >= 2 and item["barcode"])
    initial_stock = product["stock_quantity"]

    sale_response = client.post(
        "/sales",
        headers=auth_headers,
        json={
            "items": [{"product_id": product["id"], "quantity": 2, "discount": 0}],
            "discount": 0,
            "payment_method": "PIX",
        },
    )

    assert sale_response.status_code == 201, sale_response.text
    sale_payload = sale_response.json()
    assert sale_payload["payment_method"] == "PIX"
    assert sale_payload["items"][0]["quantity"] == 2

    inventory = client.get("/inventory", headers=auth_headers).json()
    updated_product = next(item for item in inventory if item["product_id"] == product["id"])
    assert updated_product["stock_quantity"] == initial_stock - 2

    movements = client.get("/inventory/movements", headers=auth_headers).json()
    assert any(item["reason"] == f"Venda #{sale_payload['id']}" for item in movements)


def test_cash_sale_returns_change(client, auth_headers):
    products = client.get("/products", headers=auth_headers).json()
    product = next(item for item in products if item["stock_quantity"] >= 1)

    sale_response = client.post(
        "/sales",
        headers=auth_headers,
        json={
            "items": [{"product_id": product["id"], "quantity": 1, "discount": 0}],
            "discount": 0,
            "payment_method": "DINHEIRO",
            "amount_received": product["sale_price"] + 10,
        },
    )

    assert sale_response.status_code == 201, sale_response.text
    payload = sale_response.json()
    assert payload["change_amount"] == 10


def test_sale_rejects_insufficient_stock(client, auth_headers):
    products = client.get("/products", headers=auth_headers).json()
    product = next(item for item in products if item["stock_quantity"] >= 1)

    response = client.post(
        "/sales",
        headers=auth_headers,
        json={
            "items": [{"product_id": product["id"], "quantity": product["stock_quantity"] + 999, "discount": 0}],
            "discount": 0,
            "payment_method": "PIX",
        },
    )

    assert response.status_code == 400
    assert "Estoque insuficiente" in response.json()["detail"]
