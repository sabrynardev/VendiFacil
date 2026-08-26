def test_get_product_by_barcode(client, auth_headers):
    products_response = client.get("/products", headers=auth_headers)
    assert products_response.status_code == 200

    product = next(item for item in products_response.json() if item["barcode"])
    response = client.get(f"/products/barcode/{product['barcode']}", headers=auth_headers)

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == product["id"]
    assert payload["name"] == product["name"]
