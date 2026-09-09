from datetime import date, datetime, timedelta

from app.database.session import SessionLocal
from app.models.intelligence import AssistantQueryLog
from app.models.purchase import ProductSupplier
from app.models.sale import Sale


def create_product(client, headers, name, sku, sale_price=10, cost_price=5, stock=40, minimum=2):
    category = client.get("/categories", headers=headers).json()[0]
    response = client.post("/products", headers=headers, json={"name": name, "sku": sku, "category_id": category["id"], "cost_price": cost_price, "sale_price": sale_price, "stock_quantity": stock, "minimum_stock": minimum, "unit": "UN", "active": True})
    assert response.status_code == 201, response.text
    return response.json()


def sell(client, headers, product_id, quantity, key):
    response = client.post("/sales", headers=headers, json={"items": [{"product_id": product_id, "quantity": quantity}], "payments": [{"method": "PIX", "amount": quantity * 10}], "idempotency_key": key})
    assert response.status_code == 201, response.text
    return response.json()


def test_forecast_uses_full_window_coverage_and_replenishment(client, auth_headers):
    product = create_product(client, auth_headers, "Produto previsível", "INT-PRED", stock=40)
    first = sell(client, auth_headers, product["id"], 15, "forecast-one")
    second = sell(client, auth_headers, product["id"], 15, "forecast-two")
    supplier = client.get("/suppliers", headers=auth_headers).json()[0]
    account_id = client.get("/auth/me", headers=auth_headers).json()["account_id"]
    with SessionLocal() as db:
        db.query(Sale).filter(Sale.id == first["id"]).update({Sale.created_at: datetime.utcnow() - timedelta(days=20)})
        db.query(Sale).filter(Sale.id == second["id"]).update({Sale.created_at: datetime.utcnow() - timedelta(days=5)})
        db.add(ProductSupplier(account_id=account_id, product_id=product["id"], supplier_id=supplier["id"], preferred=True, lead_time_days=4, last_price=5))
        db.commit()

    response = client.get("/intelligence/forecast?window_days=30", headers=auth_headers)
    assert response.status_code == 200, response.text
    row = next(item for item in response.json()["products"] if item["product_id"] == product["id"])
    assert row["history_sufficient"] is True
    assert row["average_daily_sales"] == 1
    assert row["coverage_days"] == 10
    assert row["safety_stock"] == 2
    assert row["reorder_point"] == 6
    assert row["suggested_quantity"] == 3
    assert "incluindo dias sem venda" in row["explanation"]


def test_forecast_does_not_invent_with_insufficient_history(client, auth_headers):
    product = create_product(client, auth_headers, "Produto novo", "INT-NEW")
    sell(client, auth_headers, product["id"], 1, "forecast-insufficient")
    row = next(item for item in client.get("/intelligence/forecast", headers=auth_headers).json()["products"] if item["product_id"] == product["id"])
    assert row["history_sufficient"] is False
    assert row["coverage_days"] is None
    assert row["suggested_quantity"] is None
    assert "pelo menos 2 vendas" in row["explanation"]


def test_insights_are_deduplicated_explained_and_filterable(client, auth_headers):
    product = create_product(client, auth_headers, "Estoque crítico", "INT-LOW", stock=0, minimum=5)
    response = client.get("/intelligence/insights?priority=CRITICO", headers=auth_headers)
    assert response.status_code == 200, response.text
    insights = response.json()["insights"]
    assert any(item["type"] == "ESTOQUE_BAIXO" and item["entity_id"] == product["id"] for item in insights)
    assert len({item["id"] for item in insights}) == len(insights)
    assert all(item["explanation"] and item["calculated_at"] for item in insights)


def test_assistant_answers_real_data_logs_safely_and_refuses_actions(client, auth_headers):
    product = create_product(client, auth_headers, "Venda assistida", "INT-ASK", sale_price=10, cost_price=4)
    sell(client, auth_headers, product["id"], 2, "assistant-sale")
    answer = client.post("/intelligence/ask", headers=auth_headers, json={"question": "Quanto vendi hoje?"})
    assert answer.status_code == 200, answer.text
    assert "R$ 20,00" in answer.json()["answer"]
    assert answer.json()["tool"] == "get_sales_summary"
    assert answer.json()["read_only"] is True
    refused = client.post("/intelligence/ask", headers=auth_headers, json={"question": "Apaga a dívida de Maria"})
    assert refused.status_code == 200
    assert refused.json()["tool"] == "none"
    assert "não executa alterações" in refused.json()["answer"]
    with SessionLocal() as db:
        logs = db.query(AssistantQueryLog).all()
        assert len(logs) == 2
        assert {log.intent for log in logs} == {"SALES", "PROHIBITED_ACTION"}


def test_assistant_permissions_periods_and_no_data_fallback(client, auth_headers):
    created = client.post("/users", headers=auth_headers, json={"name": "Caixa IA", "email": "caixa.ia@example.com", "password": "caixa123", "role": "CAIXA", "active": True})
    assert created.status_code == 201
    login = client.post("/auth/login", json={"email": "caixa.ia@example.com", "password": "caixa123"}).json()
    cashier = {"Authorization": f"Bearer {login['access_token']}"}
    blocked = client.post("/intelligence/ask", headers=cashier, json={"question": "Quanto lucrei este mês?"})
    assert blocked.status_code == 200
    assert blocked.json()["blocked"] is True
    assert "não possui acesso" in blocked.json()["answer"]
    old = date.today() - timedelta(days=700)
    empty = client.post("/intelligence/ask", headers=auth_headers, json={"question": "Quanto vendi?", "start": old.isoformat(), "end": old.isoformat()})
    assert empty.status_code == 200
    assert "Não há vendas" in empty.json()["answer"]


def test_assistant_never_reads_another_account(client, auth_headers):
    registered = client.post("/accounts/register", json={"account_name": "Outra Loja", "admin_name": "Outra Admin", "admin_email": "outra@example.com", "password": "senha123", "with_default_categories": True})
    assert registered.status_code == 201, registered.text
    other_headers = {"Authorization": f"Bearer {registered.json()['access_token']}"}
    assert client.post("/cash-registers/open", headers=other_headers, json={"opening_balance": 0}).status_code == 201
    product = create_product(client, other_headers, "Produto exclusivo", "OTHER-ONLY", stock=10)
    sell(client, other_headers, product["id"], 2, "other-account-sale")

    own_answer = client.post("/intelligence/ask", headers=auth_headers, json={"question": "Quanto vendi hoje?"})
    assert own_answer.status_code == 200
    assert "Produto exclusivo" not in own_answer.json()["answer"]
    assert "Não há vendas" in own_answer.json()["answer"]


def test_assistant_rate_limit_is_scoped_per_user(client):
    registered = client.post("/accounts/register", json={"account_name": "Loja Rate", "admin_name": "Admin Rate", "admin_email": "rate@example.com", "password": "senha123", "with_default_categories": True})
    headers = {"Authorization": f"Bearer {registered.json()['access_token']}"}
    for index in range(20):
        response = client.post("/intelligence/ask", headers=headers, json={"question": f"Apagar produto {index}"})
        assert response.status_code == 200
    limited = client.post("/intelligence/ask", headers=headers, json={"question": "Apagar mais um produto"})
    assert limited.status_code == 429
    assert "Aguarde um minuto" in limited.json()["detail"]
