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
            "unit": "UN",
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


def _product_payload(category_id: int, *, name: str = "Café Especial", sku: str = "CAFE-500", barcode: str | None = "789100000001"):
    return {
        "name": name,
        "brand": "Vendi",
        "sku": sku,
        "barcode": barcode,
        "category_id": category_id,
        "cost_price": 10,
        "sale_price": 15,
        "stock_quantity": 5,
        "minimum_stock": 2,
        "unit": "UN",
        "active": True,
    }


def test_product_identifiers_are_unique_with_friendly_messages(client, auth_headers):
    category_id = client.get("/categories", headers=auth_headers).json()[0]["id"]
    created = client.post("/products", headers=auth_headers, json=_product_payload(category_id))
    assert created.status_code == 201, created.text

    duplicate_sku = client.post(
        "/products", headers=auth_headers, json=_product_payload(category_id, name="Outro café", barcode="789100000002")
    )
    assert duplicate_sku.status_code == 409
    assert "SKU" in duplicate_sku.json()["detail"]

    duplicate_barcode = client.post(
        "/products", headers=auth_headers, json=_product_payload(category_id, name="Terceiro café", sku="CAFE-501")
    )
    assert duplicate_barcode.status_code == 409
    assert "código de barras" in duplicate_barcode.json()["detail"]


def test_product_search_filters_and_standard_unit(client, auth_headers):
    category_id = client.get("/categories", headers=auth_headers).json()[0]["id"]
    created = client.post("/products", headers=auth_headers, json=_product_payload(category_id))
    assert created.status_code == 201
    assert created.json()["unit"] == "UN"
    assert created.json()["margin"] == 5
    assert created.json()["margin_percent"] == 33.33

    by_sku = client.get("/products", headers=auth_headers, params={"search": "CAFE-500"}).json()
    assert [item["id"] for item in by_sku] == [created.json()["id"]]
    by_category = client.get("/products", headers=auth_headers, params={"category_id": category_id}).json()
    assert created.json()["id"] in {item["id"] for item in by_category}


def test_product_rejects_negative_price_and_fractional_unit_stock(client, auth_headers):
    category_id = client.get("/categories", headers=auth_headers).json()[0]["id"]
    negative_price = _product_payload(category_id)
    negative_price["sale_price"] = -1
    assert client.post("/products", headers=auth_headers, json=negative_price).status_code == 422

    fractional_stock = _product_payload(category_id)
    fractional_stock["stock_quantity"] = 1.5
    assert client.post("/products", headers=auth_headers, json=fractional_stock).status_code == 422


def test_manual_movement_rejects_fractional_quantity_for_unit_product(client, auth_headers):
    category_id = client.get("/categories", headers=auth_headers).json()[0]["id"]
    product = client.post("/products", headers=auth_headers, json=_product_payload(category_id)).json()
    response = client.post(
        "/inventory/movement",
        headers=auth_headers,
        json={"product_id": product["id"], "quantity": 0.5, "type": "saida", "reason": "Teste"},
    )
    assert response.status_code == 400
    assert "quantidades inteiras" in response.json()["detail"]


def test_sale_and_manual_adjustment_create_traceable_movements(client, auth_headers):
    category_id = client.get("/categories", headers=auth_headers).json()[0]["id"]
    product = client.post("/products", headers=auth_headers, json=_product_payload(category_id)).json()
    sale = client.post(
        "/sales",
        headers=auth_headers,
        json={"items": [{"product_id": product["id"], "quantity": 2, "discount": 0}], "discount": 0, "payment_method": "PIX"},
    )
    assert sale.status_code == 201, sale.text

    adjustment = client.post(
        "/inventory/movement",
        headers=auth_headers,
        json={"product_id": product["id"], "quantity": 1, "target_stock": 4, "type": "ajuste", "reason": "Contagem"},
    )
    assert adjustment.status_code == 201, adjustment.text
    assert adjustment.json()["previous_stock"] == 3
    assert adjustment.json()["new_stock"] == 4

    movements = client.get("/inventory/movements", headers=auth_headers).json()
    sale_movement = next(item for item in movements if item["reference_type"] == "sale")
    assert sale_movement["reference_id"] == sale.json()["id"]
    assert sale_movement["type"] == "venda"
