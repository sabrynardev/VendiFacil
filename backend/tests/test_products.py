def test_get_product_by_barcode(client, auth_headers):
    products_response = client.get("/products", headers=auth_headers)
    assert products_response.status_code == 200

    product = next(item for item in products_response.json() if item["barcode"])
    response = client.get(f"/products/barcode/{product['barcode']}", headers=auth_headers)

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == product["id"]
    assert payload["name"] == product["name"]


def test_delete_product_without_history_removes_it(client, auth_headers):
    categories = client.get("/categories", headers=auth_headers).json()
    created = client.post(
        "/products",
        headers=auth_headers,
        json={
            "name": "Produto temporário",
            "sku": "TEMP-DELETE",
            "category_id": categories[0]["id"],
            "cost_price": 2,
            "sale_price": 4,
            "stock_quantity": 0,
            "minimum_stock": 0,
            "unit": "unidade",
            "active": True,
        },
    )
    assert created.status_code == 201, created.text

    response = client.delete(f"/products/{created.json()['id']}", headers=auth_headers)

    assert response.status_code == 204
    product_ids = {product["id"] for product in client.get("/products", headers=auth_headers).json()}
    assert created.json()["id"] not in product_ids


def test_delete_sold_product_archives_and_preserves_sale(client, auth_headers):
    product = next(product for product in client.get("/products", headers=auth_headers).json() if product["stock_quantity"] >= 1)
    sale = client.post(
        "/sales",
        headers=auth_headers,
        json={
            "items": [{"product_id": product["id"], "quantity": 1, "discount": 0}],
            "discount": 0,
            "payment_method": "PIX",
        },
    )
    assert sale.status_code == 201, sale.text

    response = client.delete(f"/products/{product['id']}", headers=auth_headers)

    assert response.status_code == 204
    product_ids = {item["id"] for item in client.get("/products", headers=auth_headers).json()}
    assert product["id"] not in product_ids
    sales = client.get("/sales", headers=auth_headers)
    assert sales.status_code == 200
    assert any(item["id"] == sale.json()["id"] for item in sales.json())
