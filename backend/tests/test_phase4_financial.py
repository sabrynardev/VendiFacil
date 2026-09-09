from datetime import date, timedelta


def categories(client, headers):
    items = client.get("/financial/categories", headers=headers).json()
    expense = next(item for item in items if item["type"] == "DESPESA" and item["name"] == "Outros")
    supplier = next(item for item in items if item["type"] == "DESPESA" and item["name"] == "Fornecedores")
    revenue = next(item for item in items if item["type"] == "RECEITA" and item["name"] == "Outras receitas")
    return expense, supplier, revenue


def create_payable(client, headers, category_id, **overrides):
    payload = {"description": "Conta de energia", "category_id": category_id, "amount": 1000, "due_date": date.today().isoformat(), "notes": "Competência atual"}
    payload.update(overrides)
    response = client.post("/financial/payables", headers=headers, json=payload)
    assert response.status_code == 201, response.text
    return response.json()


def test_payable_partial_full_idempotency_and_invalid_amount(client, auth_headers):
    expense, _, _ = categories(client, auth_headers)
    payable = create_payable(client, auth_headers, expense["id"])
    partial = client.post(f"/financial/payables/{payable['id']}/payments", headers=auth_headers, json={"amount": 600, "method": "PIX", "idempotency_key": "partial-payment-001"})
    assert partial.status_code == 201, partial.text
    repeated = client.post(f"/financial/payables/{payable['id']}/payments", headers=auth_headers, json={"amount": 600, "method": "PIX", "idempotency_key": "partial-payment-001"})
    assert repeated.status_code == 201
    detail = next(item for item in client.get("/financial/payables", headers=auth_headers).json() if item["id"] == payable["id"])
    assert detail["paid_amount"] == 600
    assert detail["balance"] == 400
    assert detail["status"] == "PARCIAL"
    excessive = client.post(f"/financial/payables/{payable['id']}/payments", headers=auth_headers, json={"amount": 401, "method": "PIX"})
    assert excessive.status_code == 400
    paid = client.post(f"/financial/payables/{payable['id']}/payments", headers=auth_headers, json={"amount": 400, "method": "PIX", "idempotency_key": "final-payment-001"})
    assert paid.status_code == 201
    detail = next(item for item in client.get("/financial/payables", headers=auth_headers).json() if item["id"] == payable["id"])
    assert detail["status"] == "PAGA"
    assert detail["balance"] == 0
    assert client.post(f"/financial/payables/{payable['id']}/payments", headers=auth_headers, json={"amount": 1, "method": "PIX"}).status_code == 400


def test_overdue_cancel_and_cash_register_payment(client, auth_headers):
    expense, _, _ = categories(client, auth_headers)
    overdue = create_payable(client, auth_headers, expense["id"], description="Internet vencida", amount=50, due_date=(date.today() - timedelta(days=2)).isoformat())
    detail = next(item for item in client.get("/financial/payables", headers=auth_headers).json() if item["id"] == overdue["id"])
    assert detail["status"] == "VENCIDA"
    cancelled = client.post(f"/financial/payables/{overdue['id']}/cancel?reason=Lançamento duplicado", headers=auth_headers)
    assert cancelled.status_code == 200
    assert cancelled.json()["status"] == "CANCELADA"

    cash = create_payable(client, auth_headers, expense["id"], description="Gelo emergencial", amount=20)
    paid = client.post(f"/financial/payables/{cash['id']}/payments", headers=auth_headers, json={"amount": 20, "method": "DINHEIRO", "use_cash_register": True})
    assert paid.status_code == 201, paid.text
    register = client.get("/cash-registers/current", headers=auth_headers).json()
    assert register["summary"]["withdrawals"] == 20


def test_purchase_payable_uses_order_total_and_prevents_duplicate(client, auth_headers):
    product = client.get("/products", headers=auth_headers).json()[0]
    supplier = client.get("/suppliers", headers=auth_headers).json()[0]
    order = client.post("/purchases", headers=auth_headers, json={"supplier_id": supplier["id"], "items": [{"product_id": product["id"], "quantity": 3, "unit_cost": 10}]}).json()
    _, supplier_category, _ = categories(client, auth_headers)
    payload = {"description": "Compra para estoque", "category_id": supplier_category["id"], "amount": 1, "due_date": (date.today() + timedelta(days=14)).isoformat(), "purchase_order_id": order["id"]}
    created = client.post("/financial/payables", headers=auth_headers, json=payload)
    assert created.status_code == 201, created.text
    assert created.json()["original_amount"] == 30
    assert created.json()["supplier_id"] == supplier["id"]
    assert created.json()["affects_result"] is False
    assert client.post("/financial/payables", headers=auth_headers, json=payload).status_code == 400


def test_recurring_generation_is_not_duplicated(client, auth_headers):
    expense, _, _ = categories(client, auth_headers)
    recurring = client.post("/financial/recurring", headers=auth_headers, json={"description": "Aluguel recorrente", "category_id": expense["id"], "amount": 800, "frequency": "MENSAL", "next_due_date": date.today().isoformat()})
    assert recurring.status_code == 201, recurring.text
    first = client.post("/financial/recurring/generate", headers=auth_headers)
    second = client.post("/financial/recurring/generate", headers=auth_headers)
    assert len(first.json()) == 1
    assert second.json() == []


def test_financial_scenario_separates_revenue_cash_cmv_and_credit_receipt(client, auth_headers):
    category = client.get("/categories", headers=auth_headers).json()[0]
    cash_product = client.post("/products", headers=auth_headers, json={"name":"Produto dinheiro","sku":"FIN-CASH","category_id":category["id"],"cost_price":60,"sale_price":100,"stock_quantity":5,"minimum_stock":1,"unit":"UN","active":True}).json()
    credit_product = client.post("/products", headers=auth_headers, json={"name":"Produto fiado","sku":"FIN-CREDIT","category_id":category["id"],"cost_price":50,"sale_price":100,"stock_quantity":5,"minimum_stock":1,"unit":"UN","active":True}).json()
    customer = client.post("/customers", headers=auth_headers, json={"name":"Cliente Financeiro","credit_limit":500,"credit_blocked":False,"active":True}).json()
    cash_sale = client.post("/sales", headers=auth_headers, json={"items":[{"product_id":cash_product["id"],"quantity":1}],"payments":[{"method":"DINHEIRO","amount":100,"amount_received":100}],"idempotency_key":"financial-cash-sale"})
    credit_sale = client.post("/sales", headers=auth_headers, json={"items":[{"product_id":credit_product["id"],"quantity":1}],"payments":[{"method":"FIADO","amount":100}],"customer_id":customer["id"],"idempotency_key":"financial-credit-sale"})
    assert cash_sale.status_code == credit_sale.status_code == 201
    changed_cost = {key: credit_product.get(key) for key in ["name", "brand", "description", "sku", "barcode", "category_id", "supplier_id", "sale_price", "stock_quantity", "minimum_stock", "unit", "active"]}
    changed_cost["cost_price"] = 999
    assert client.put(f"/products/{credit_product['id']}", headers=auth_headers, json=changed_cost).status_code == 200
    expense, _, _ = categories(client, auth_headers)
    payable = create_payable(client, auth_headers, expense["id"], description="Despesa operacional", amount=20)
    assert client.post(f"/financial/payables/{payable['id']}/payments", headers=auth_headers, json={"amount":20,"method":"PIX"}).status_code == 201
    today = date.today().isoformat()
    summary = client.get(f"/financial/summary?start={today}&end={today}", headers=auth_headers).json()
    assert summary["revenue"] == 200
    assert summary["received_sales"] == 100
    assert summary["credit_sales"] == 100
    assert summary["cmv"] == 110
    assert summary["gross_profit"] == 90
    assert summary["operational_expenses"] == 20
    assert summary["estimated_result"] == 70
    assert summary["cash_in"] == 100

    payment = client.post(f"/customers/{customer['id']}/payments", headers=auth_headers, json={"amount":100,"method":"PIX"})
    assert payment.status_code == 201
    updated = client.get(f"/financial/summary?start={today}&end={today}", headers=auth_headers).json()
    assert updated["revenue"] == 200
    assert updated["credit_receipts"] == 100
    assert updated["cash_in"] == 200


def test_manual_revenue_receivable_projection_and_cash_flow(client, auth_headers):
    _, _, revenue_category = categories(client, auth_headers)
    revenue = client.post("/financial/revenues", headers=auth_headers, json={"description":"Venda de equipamento","category_id":revenue_category["id"],"amount":300,"payment_method":"PIX","idempotency_key":"manual-revenue-001"})
    assert revenue.status_code == 201, revenue.text
    repeated = client.post("/financial/revenues", headers=auth_headers, json={"description":"Venda de equipamento","category_id":revenue_category["id"],"amount":300,"payment_method":"PIX","idempotency_key":"manual-revenue-001"})
    assert repeated.json()["id"] == revenue.json()["id"]
    receivable = client.post("/financial/receivables", headers=auth_headers, json={"description":"Recebível futuro","category_id":revenue_category["id"],"amount":200,"due_date":(date.today()+timedelta(days=5)).isoformat()})
    assert receivable.status_code == 201, receivable.text
    receipt = client.post(f"/financial/receivables/{receivable.json()['source_id']}/receipts", headers=auth_headers, json={"amount":50,"method":"PIX","idempotency_key":"receivable-001"})
    assert receipt.status_code == 201, receipt.text
    projections = client.get("/financial/projections", headers=auth_headers).json()
    assert projections[0]["receivables"] == 150
    today=date.today().isoformat(); flow=client.get(f"/financial/cash-flow?start={today}&end={today}",headers=auth_headers).json()
    assert any(item["source"]=="RECEITA_MANUAL" and item["amount"]==300 for item in flow)
    assert any(item["source"]=="CONTA_RECEBER" and item["amount"]==50 for item in flow)
