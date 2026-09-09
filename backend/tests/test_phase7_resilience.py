from datetime import datetime, timedelta, timezone
from uuid import uuid4


def offline_payload(product, register_id, **overrides):
    quantity = overrides.pop("quantity", 1)
    unit_price = overrides.pop("unit_price", product["sale_price"])
    operation_id = str(uuid4())
    payload = {
        "operation_id": operation_id,
        "idempotency_key": str(uuid4()),
        "device_id": "CAIXA-TESTE-001",
        "local_created_at": datetime.now(timezone.utc).isoformat(),
        "cash_register_id": register_id,
        "items": [{"product_id": product["id"], "quantity": quantity, "unit_price": unit_price, "discount": 0, "product_updated_at": product["updated_at"]}],
        "discount": 0,
        "surcharge": 0,
        "payments": [{"method": "PIX", "amount": round(quantity * unit_price, 2)}],
        **overrides,
    }
    return payload


def operation_context(client, headers):
    product = next(item for item in client.get("/products", headers=headers).json() if item["stock_quantity"] >= 2)
    register = client.get("/cash-registers/current", headers=headers).json()
    return product, register


def test_offline_sync_is_idempotent_and_does_not_duplicate_stock_movement(client, auth_headers):
    product, register = operation_context(client, auth_headers)
    before = product["stock_quantity"]
    payload = offline_payload(product, register["id"])

    first = client.post("/sync/sales", headers=auth_headers, json=payload)
    repeated = client.post("/sync/sales", headers=auth_headers, json=payload)

    assert first.status_code == 200, first.text
    assert repeated.status_code == 200, repeated.text
    assert repeated.json()["duplicate"] is True
    assert repeated.json()["sale"]["id"] == first.json()["sale"]["id"]
    updated = next(item for item in client.get("/products", headers=auth_headers).json() if item["id"] == product["id"])
    assert updated["stock_quantity"] == before - 1


def test_offline_sync_preserves_cached_price_and_reports_price_conflict(client, auth_headers):
    product, register = operation_context(client, auth_headers)
    cached_price = product["sale_price"]
    payload = offline_payload(product, register["id"], unit_price=cached_price)
    updated_product = {**product, "sale_price": round(cached_price + 0.5, 2)}
    updated = client.put(f"/products/{product['id']}", headers=auth_headers, json=updated_product)
    assert updated.status_code == 200, updated.text

    response = client.post("/sync/sales", headers=auth_headers, json=payload)

    assert response.status_code == 200, response.text
    assert response.json()["conflict"] is True
    assert f"PRECO_ALTERADO:{product['id']}" in response.json()["conflicts"]
    assert response.json()["sale"]["items"][0]["unit_price"] == cached_price


def test_offline_sync_rejects_price_changed_without_newer_server_version(client, auth_headers):
    product, register = operation_context(client, auth_headers)
    payload = offline_payload(product, register["id"], unit_price=round(max(product["sale_price"] - 1, 0.01), 2))

    response = client.post("/sync/sales", headers=auth_headers, json=payload)

    assert response.status_code == 409
    assert response.json()["detail"]["category"] == "PRICE_INTEGRITY"


def test_offline_sync_accepts_sale_with_stock_conflict_and_records_it(client, auth_headers):
    product, register = operation_context(client, auth_headers)
    quantity = product["stock_quantity"] + 1
    payload = offline_payload(product, register["id"], quantity=quantity)

    response = client.post("/sync/sales", headers=auth_headers, json=payload)

    assert response.status_code == 200, response.text
    assert f"ESTOQUE_NEGATIVO:{product['id']}" in response.json()["conflicts"]
    logs = client.get("/sync/logs", headers=auth_headers).json()
    assert logs[0]["status"] == "SYNCED_WITH_CONFLICT"


def test_expired_offline_authorization_requires_attention_without_creating_sale(client, auth_headers):
    product, register = operation_context(client, auth_headers)
    payload = offline_payload(product, register["id"], local_created_at=(datetime.now(timezone.utc) - timedelta(hours=13)).isoformat())

    response = client.post("/sync/sales", headers=auth_headers, json=payload)

    assert response.status_code == 409
    assert response.json()["detail"]["category"] == "OFFLINE_SESSION_EXPIRED"
    logs = client.get("/sync/logs", headers=auth_headers).json()
    assert logs[0]["operation_id"] == payload["operation_id"]
    assert logs[0]["status"] == "REQUIRES_ATTENTION"
