import math
import re
import time as clock
import unicodedata
from collections import defaultdict, deque
from datetime import date, datetime, time, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.core.config import get_settings
from app.core.datetime import local_today
from app.core.permissions import PermissionCode
from app.models.intelligence import AssistantQueryLog
from app.models.purchase import ProductSupplier
from app.models.sale import Sale, SaleItem, SaleStatus
from app.models.user import User
from app.services.analytics import analytics_overview, bounds, loss_and_expiry_analytics, product_analytics
from app.services.profiles import permission_codes_for_user

settings = get_settings()

PRIORITY_ORDER = {"CRITICO": 0, "IMPORTANTE": 1, "ATENCAO": 2, "INFORMATIVO": 3}
_requests: dict[tuple[int, int], deque[float]] = defaultdict(deque)


class IntelligenceValidationError(Exception):
    pass


def _round_quantity(value: float) -> float:
    return round(max(value, 0), 3)


def _money(value: float) -> str:
    return f"{value:,.2f}".replace(",", "#").replace(".", ",").replace("#", ".")


def stock_forecast(db: Session, account_id: int, end: date, window_days: int | None = None) -> dict:
    window = window_days or settings.intelligence_default_window_days
    if window < 7 or window > 180:
        raise IntelligenceValidationError("A janela de previsão deve ter entre 7 e 180 dias.")
    start = end - timedelta(days=window - 1)
    analytics = product_analytics(db, account_id, start, end, settings.intelligence_stopped_days)
    start_at, end_at = bounds(start, end)
    sale_rows = (
        db.query(SaleItem.product_id, SaleItem.quantity, Sale.created_at, Sale.id)
        .join(Sale)
        .filter(
            Sale.account_id == account_id,
            Sale.status == SaleStatus.COMPLETED,
            Sale.created_at.between(start_at, end_at),
        )
        .all()
    )
    event_ids: dict[int, set[int]] = defaultdict(set)
    weekday_quantity: dict[int, float] = defaultdict(float)
    weekend_quantity: dict[int, float] = defaultdict(float)
    for product_id, quantity, created_at, sale_id in sale_rows:
        event_ids[product_id].add(sale_id)
        target = weekend_quantity if created_at.weekday() >= 4 else weekday_quantity
        target[product_id] += float(quantity)
    weekdays = sum(1 for offset in range(window) if (start + timedelta(days=offset)).weekday() < 4)
    weekend_days = window - weekdays
    links = (
        db.query(ProductSupplier)
        .options(joinedload(ProductSupplier.supplier))
        .filter(ProductSupplier.account_id == account_id)
        .all()
    )
    by_product: dict[int, list[ProductSupplier]] = defaultdict(list)
    for link in links:
        by_product[link.product_id].append(link)

    rows = []
    for item in analytics["products"]:
        average = float(item["quantity"]) / window
        sale_events = len(event_ids[item["product_id"]])
        sufficient = sale_events >= 2 and average > 0
        coverage = round(float(item["stock"]) / average, 1) if sufficient else None
        candidates = sorted(by_product[item["product_id"]], key=lambda link: (not link.preferred, link.lead_time_days is None, link.lead_time_days or 9999))
        lead = next((link.lead_time_days for link in candidates if link.lead_time_days is not None), None)
        safety = math.ceil(max(float(item["minimum_stock"]), average * settings.intelligence_safety_stock_days)) if sufficient else None
        reorder_point = math.ceil(average * lead + safety) if sufficient and lead is not None and safety is not None else None
        target = math.ceil(average * (lead + settings.intelligence_purchase_horizon_days) + safety) if reorder_point is not None and lead is not None and safety is not None else None
        suggested = _round_quantity(target - float(item["stock"])) if target is not None else None
        if suggested == 0:
            suggested = 0
        weekday_average = weekday_quantity[item["product_id"]] / weekdays if weekdays else 0
        weekend_average = weekend_quantity[item["product_id"]] / weekend_days if weekend_days else 0
        seasonality = None
        if sale_events >= 4 and weekday_average > 0 and weekend_average >= weekday_average * 1.5:
            seasonality = {"pattern": "FIM_DE_SEMANA", "weekday_average": round(weekday_average, 3), "weekend_average": round(weekend_average, 3)}
        elif sale_events >= 4 and weekend_average > 0 and weekday_average >= weekend_average * 1.5:
            seasonality = {"pattern": "DIAS_UTEIS", "weekday_average": round(weekday_average, 3), "weekend_average": round(weekend_average, 3)}
        rows.append({
            **item,
            "window_days": window,
            "sale_events": sale_events,
            "history_sufficient": sufficient,
            "average_daily_sales": round(average, 3),
            "coverage_days": coverage,
            "lead_time_days": lead,
            "safety_stock": safety,
            "reorder_point": reorder_point,
            "suggested_quantity": suggested,
            "suppliers": [{"id": link.supplier_id, "name": link.supplier.name, "price": float(link.last_price) if link.last_price is not None else None, "lead_time_days": link.lead_time_days, "preferred": link.preferred} for link in candidates],
            "seasonality": seasonality,
            "explanation": (
                f"Foram vendidas {item['quantity']} unidades em {window} dias, incluindo dias sem venda. "
                f"Média: {round(average, 3)}/dia. Cobertura: {item['stock']} ÷ {round(average, 3)} = {coverage} dias."
                if sufficient
                else f"São necessárias pelo menos 2 vendas no período de {window} dias para estimar a demanda."
            ),
        })
    return {"period": {"start": start.isoformat(), "end": end.isoformat(), "window_days": window}, "products": rows}


def _insight(kind: str, title: str, message: str, priority: str, category: str, entity_type: str | None, entity_id: int | None, period: dict, explanation: str, data: dict, action: dict | None = None) -> dict:
    return {"id": f"{kind}:{entity_type or 'GERAL'}:{entity_id or 0}", "type": kind, "title": title, "message": message, "priority": priority, "category": category, "entity_type": entity_type, "entity_id": entity_id, "period": period, "calculated_at": datetime.utcnow().isoformat(), "explanation": explanation, "data": data, "action": action}


def generate_insights(db: Session, account_id: int, start: date, end: date, window_days: int | None = None) -> dict:
    overview = analytics_overview(db, account_id, start, end, settings.intelligence_stopped_days)
    forecast = stock_forecast(db, account_id, end, window_days)
    period = overview["period"]
    insights = []
    for item in forecast["products"]:
        product_data = {key: item[key] for key in ["stock", "minimum_stock", "average_daily_sales", "coverage_days", "lead_time_days", "safety_stock", "reorder_point", "suggested_quantity", "history_sufficient"]}
        if item["stock"] <= item["minimum_stock"]:
            insights.append(_insight("ESTOQUE_BAIXO", "Estoque abaixo do mínimo", f"{item['product']} possui {item['stock']} em estoque; mínimo configurado: {item['minimum_stock']}.", "CRITICO" if item["stock"] <= 0 else "IMPORTANTE", "Estoque", "PRODUCT", item["product_id"], period, "Comparamos o estoque atual ao estoque mínimo cadastrado.", product_data, {"label": "Ver produto", "path": "/products"}))
        if item["history_sufficient"] and item["coverage_days"] is not None and item["coverage_days"] <= 7:
            priority = "CRITICO" if item["coverage_days"] <= 3 else "IMPORTANTE"
            insights.append(_insight("RISCO_RUPTURA", "Estoque pode acabar em breve", f"{item['product']} possui aproximadamente {item['coverage_days']} dias de cobertura.", priority, "Estoque", "PRODUCT", item["product_id"], period, item["explanation"], product_data, {"label": "Ver estoque", "path": "/inventory"}))
        if item["suggested_quantity"] and item["reorder_point"] is not None and item["stock"] <= item["reorder_point"]:
            explanation = f"Ponto de pedido: média {item['average_daily_sales']}/dia × prazo {item['lead_time_days']} dias + segurança {item['safety_stock']} = {item['reorder_point']}. A sugestão cobre também {settings.intelligence_purchase_horizon_days} dias até a próxima revisão."
            insights.append(_insight("REPOSICAO", "Reposição sugerida", f"Considere comprar aproximadamente {item['suggested_quantity']} de {item['product']} após revisar fornecedor e prazo.", "IMPORTANTE", "Estoque", "PRODUCT", item["product_id"], period, explanation, product_data, {"label": "Criar pedido em rascunho", "path": "/purchases"}))
        if item["history_sufficient"] and item["coverage_days"] is not None and item["coverage_days"] >= 90:
            insights.append(_insight("EXCESSO_ESTOQUE", "Cobertura de estoque elevada", f"{item['product']} possui aproximadamente {item['coverage_days']} dias de vendas no ritmo recente.", "ATENCAO", "Estoque", "PRODUCT", item["product_id"], period, item["explanation"], product_data, {"label": "Ver relatório", "path": "/reports"}))
        if item["seasonality"]:
            label = "entre sexta-feira e domingo" if item["seasonality"]["pattern"] == "FIM_DE_SEMANA" else "de segunda a quinta-feira"
            insights.append(_insight("DEMANDA_VARIACAO", "Ritmo de venda varia na semana", f"{item['product']} apresenta média maior {label}.", "INFORMATIVO", "Vendas", "PRODUCT", item["product_id"], period, f"Média de segunda a quinta: {item['seasonality']['weekday_average']}/dia. Média de sexta a domingo: {item['seasonality']['weekend_average']}/dia. O alerta exige ao menos 4 vendas e diferença de 50%.", item["seasonality"], {"label": "Ver relatório", "path": "/reports"}))

    for item in overview["products"]["stopped"][:10]:
        insights.append(_insight("PRODUTO_PARADO", "Produto sem saída", f"{item['product']} está sem venda há {item['days_without_sale']} dias e representa R$ {_money(item['stopped_value'])} em estoque a custo.", "ATENCAO", "Estoque", "PRODUCT", item["product_id"], period, "Usamos a última venda registrada, o estoque atual e o custo unitário atual.", {"days_without_sale": item["days_without_sale"], "stock": item["stock"], "stopped_value": item["stopped_value"]}, {"label": "Ver relatório", "path": "/reports"}))
    for item in overview["products"]["top_revenue"]:
        if item["margin"] < 10:
            insights.append(_insight("MARGEM_BAIXA", "Margem merece atenção", f"{item['product']} faturou R$ {_money(item['revenue'])}, com margem bruta de {item['margin']:.1f}%.", "IMPORTANTE" if item["margin"] < 5 else "ATENCAO", "Vendas", "PRODUCT", item["product_id"], period, "Margem = (faturamento líquido - custo histórico vendido) ÷ faturamento líquido.", {"revenue": item["revenue"], "cmv": item["cmv"], "margin": item["margin"]}, {"label": "Ver produto", "path": "/products"}))
    for item in overview["suppliers"]["cost_changes"]:
        if item["variation"] >= settings.intelligence_cost_alert_percent and len(item["records"]) >= 2:
            insights.append(_insight("CUSTO_AUMENTANDO", "Custo de compra aumentou", f"O custo de {item['product']} em {item['supplier']} aumentou {item['variation']:.1f}% no período.", "IMPORTANTE" if item["variation"] >= 15 else "ATENCAO", "Fornecedores", "PRODUCT", item["product_id"], period, f"Comparamos R$ {_money(item['first_cost'])} com R$ {_money(item['last_cost'])} em {len(item['records'])} registros.", {"first_cost": item["first_cost"], "last_cost": item["last_cost"], "variation": item["variation"], "records": len(item["records"])}, {"label": "Ver fornecedor", "path": "/suppliers"}))

    previous_losses = loss_and_expiry_analytics(db, account_id, date.fromisoformat(period["previous_start"]), date.fromisoformat(period["previous_end"]), 0)
    current_loss = overview["losses"]["total_value"]
    previous_loss = previous_losses["total_value"]
    if current_loss > 0:
        change = None if previous_loss == 0 else round((current_loss - previous_loss) / previous_loss * 100, 2)
        if change is None or change >= 20:
            insights.append(_insight("PERDA_ELEVADA", "Perdas registradas no período", f"As perdas somaram R$ {_money(current_loss)}." + (f" Variação de {change:+.1f}% contra o período anterior." if change is not None else " Não há base anterior para comparação."), "IMPORTANTE" if change is not None and change >= 50 else "ATENCAO", "Perdas", None, None, period, "Somamos quantidade × custo congelado de cada baixa e comparamos períodos equivalentes.", {"current": current_loss, "previous": previous_loss, "variation": change}, {"label": "Ver perdas", "path": "/reports"}))
    expiry = overview["losses"]["expiry_risk"]
    expiring = next((item for item in expiry if item["range"] == "ATE_3_DIAS"), None)
    if expiring and expiring["quantity"] > 0:
        insights.append(_insight("VALIDADE", "Produtos vencem em até 3 dias", f"{expiring['quantity']} unidades, equivalentes a R$ {_money(expiring['value'])} a custo, vencem em até 3 dias.", "CRITICO", "Perdas", None, None, period, "Somamos os lotes ativos com validade entre hoje e os próximos 3 dias.", expiring, {"label": "Ver lotes", "path": "/lots"}))
    if overview["credit"]["open_total"] > 0:
        debtors = overview["credit"]["top_debtors"][:3]
        concentrated = round(sum(item["balance"] for item in debtors) / overview["credit"]["open_total"] * 100, 1) if debtors else 0
        insights.append(_insight("FIADO_ATRASADO", "Fiado em aberto", f"Há R$ {_money(overview['credit']['open_total'])} em aberto; R$ {_money(overview['credit']['overdue_total'])} estão vencidos.", "IMPORTANTE" if overview["credit"]["overdue_total"] > 0 else "INFORMATIVO", "Clientes", None, None, period, f"Somamos apenas dívidas abertas ou parciais. Os 3 maiores saldos representam {concentrated}% do total.", {"open_total": overview["credit"]["open_total"], "overdue_total": overview["credit"]["overdue_total"], "top_three_concentration": concentrated}, {"label": "Ver clientes", "path": "/customers"}))
    revenue_change = overview["comparisons"]["revenue"]
    if revenue_change is not None and abs(revenue_change) >= 5:
        direction = "aumentou" if revenue_change > 0 else "caiu"
        contribution_text = ""
        contribution_data = []
        if revenue_change < 0:
            previous_products = product_analytics(db, account_id, date.fromisoformat(period["previous_start"]), date.fromisoformat(period["previous_end"]), settings.intelligence_stopped_days)["products"]
            current_revenue = {item["product_id"]: item["revenue"] for item in overview["products"]["products"]}
            declines = sorted(({"product": item["product"], "change": round(current_revenue.get(item["product_id"], 0) - item["revenue"], 2)} for item in previous_products), key=lambda item: item["change"])
            contribution_data = [item for item in declines if item["change"] < 0][:3]
            if contribution_data:
                contribution_text = " Maiores reduções: " + ", ".join(f"{item['product']} (R$ {_money(abs(item['change']))})" for item in contribution_data) + "."
        insights.append(_insight("FATURAMENTO_VARIACAO", "Variação de faturamento", f"O faturamento {direction} {abs(revenue_change):.1f}% em relação ao período anterior equivalente.{contribution_text}", "INFORMATIVO" if revenue_change > 0 else "ATENCAO", "Vendas", None, None, period, "Comparamos o faturamento líquido de períodos com a mesma quantidade de dias. As contribuições mostram onde a variação ocorreu, mas os dados não permitem afirmar causas externas.", {"current": overview["summary"]["revenue"], "variation": revenue_change, "product_contributions": contribution_data}, {"label": "Ver relatório", "path": "/reports"}))
    insights.sort(key=lambda item: (PRIORITY_ORDER[item["priority"]], item["title"], item["id"]))
    return {"period": period, "calculated_at": datetime.utcnow().isoformat(), "forecast": forecast, "insights": insights}


def _normalize(value: str) -> str:
    return "".join(char for char in unicodedata.normalize("NFD", value.lower()) if unicodedata.category(char) != "Mn")


def interpret_period(question: str, start: date | None = None, end: date | None = None) -> tuple[date, date, str]:
    text = _normalize(question)
    today = local_today()
    if "ontem" in text:
        day = today - timedelta(days=1); return day, day, "ontem"
    if "hoje" in text:
        return today, today, "hoje"
    if "semana passada" in text:
        end_day = today - timedelta(days=today.weekday() + 1); return end_day - timedelta(days=6), end_day, "semana passada"
    if "esta semana" in text:
        return today - timedelta(days=today.weekday()), today, "esta semana"
    if "mes passado" in text:
        end_day = today.replace(day=1) - timedelta(days=1); return end_day.replace(day=1), end_day, "mês passado"
    if "este mes" in text or "nesse mes" in text:
        return today.replace(day=1), today, "este mês"
    if start and end:
        bounds(start, end)
        return start, end, "período selecionado"
    match = re.search(r"ultimos\s+(\d+)\s+dias", text)
    days = min(max(int(match.group(1)), 1), 730) if match else 30
    return today - timedelta(days=days - 1), today, f"últimos {days} dias"


def enforce_rate_limit(user: User, limit: int = 20, interval_seconds: int = 60) -> None:
    key = (user.account_id, user.id)
    now = clock.monotonic()
    bucket = _requests[key]
    while bucket and now - bucket[0] >= interval_seconds:
        bucket.popleft()
    if len(bucket) >= limit:
        raise IntelligenceValidationError("Muitas consultas em pouco tempo. Aguarde um minuto e tente novamente.")
    bucket.append(now)


def ask_vendi(db: Session, user: User, question: str, start: date | None = None, end: date | None = None) -> dict:
    started = clock.perf_counter()
    enforce_rate_limit(user)
    question = question.strip()[:500]
    if not question:
        raise IntelligenceValidationError("Digite uma pergunta para o Vendi.")
    text = _normalize(question)
    period_start, period_end, period_label = interpret_period(question, start, end)
    permissions = set(permission_codes_for_user(user))
    forbidden = any(term in text for term in ["apaga", "apagar", "exclui", "excluir", "cancela", "cancelar", "altera", "alterar", "fecha o caixa", "paga a conta", "baixar a divida", "criar usuario"])
    intent = "PROHIBITED_ACTION" if forbidden else "UNKNOWN"
    tool = "none"
    blocked = False
    sources: list[str] = []

    def allowed(*codes: PermissionCode) -> bool:
        return any(code.value in permissions for code in codes)

    if forbidden:
        answer = "O Pergunte ao Vendi é somente para consultas e não executa alterações. Use o fluxo tradicional correspondente, com confirmação e permissão apropriadas."
    elif any(term in text for term in ["lucro", "lucrei", "margem", "resultado", "cmv"]):
        intent, tool = "PROFIT", "get_margin_summary"
        if not allowed(PermissionCode.FINANCIAL_PROFIT_VIEW, PermissionCode.PROFIT_VIEW):
            blocked = True; answer = "Seu perfil não possui acesso a informações de lucro e margem."
        else:
            data = analytics_overview(db, user.account_id, period_start, period_end)
            sources = ["Vendas", "Custos históricos", "Financeiro"]
            if not data["summary"]["sales_count"]:
                answer = f"Não há vendas concluídas em {period_label}; por isso não há lucro disponível para esse período."
            elif "categoria" in text:
                categories = sorted(data["products"]["categories"], key=lambda item: item["profit"], reverse=True)
                answer = f"Em {period_label}, {categories[0]['category']} teve o maior lucro bruto estimado entre as categorias: R$ {_money(categories[0]['profit'])}, com margem de {categories[0]['margin']:.1f}%." if categories else f"Não há categorias com vendas em {period_label}."
            else:
                answer = f"Em {period_label} ({period_start.strftime('%d/%m/%Y')} a {period_end.strftime('%d/%m/%Y')}), o lucro bruto estimado foi R$ {_money(data['summary']['gross_profit'])}, com margem de {data['summary']['gross_margin']:.1f}%. Após despesas registradas, o resultado gerencial estimado foi R$ {_money(data['summary']['estimated_result'])}."
    elif any(term in text for term in ["devendo", "fiado", "divida", "devedor", "para receber"]):
        intent, tool = "CREDIT", "get_receivables"
        if not allowed(PermissionCode.CUSTOMERS_VIEW, PermissionCode.REPORT_CUSTOMERS):
            blocked = True; answer = "Seu perfil não possui acesso às informações de clientes e fiado."
        else:
            data = analytics_overview(db, user.account_id, period_start, period_end)["credit"]
            sources = ["Fiado", "Pagamentos de clientes"]
            leaders = ", ".join(f"{item['customer']}: R$ {_money(item['balance'])}" for item in data["top_debtors"][:3])
            answer = f"Atualmente há R$ {_money(data['open_total'])} em aberto entre {data['debtor_count']} cliente(s), sendo R$ {_money(data['overdue_total'])} vencidos." + (f" Maiores saldos: {leaders}." if leaders else "")
    elif any(term in text for term in ["fornecedor", "preco", "custo aument"]):
        intent, tool = "SUPPLIER", "get_supplier_price_changes"
        if not allowed(PermissionCode.SUPPLIERS_VIEW, PermissionCode.REPORT_SUPPLIERS):
            blocked = True; answer = "Seu perfil não possui acesso às informações de fornecedores."
        else:
            rows = analytics_overview(db, user.account_id, period_start, period_end)["suppliers"]["cost_changes"]
            sources = ["Compras", "Histórico de preços de fornecedores"]
            valid = [item for item in rows if len(item["records"]) >= 2]
            answer = (f"Em {period_label}, a maior alta observada foi {valid[0]['supplier']} em {valid[0]['product']}: {valid[0]['variation']:+.1f}%, de R$ {_money(valid[0]['first_cost'])} para R$ {_money(valid[0]['last_cost'])}." if valid else f"Não há histórico suficiente de preços em {period_label} para comparar fornecedores.")
    elif any(term in text for term in ["perda", "vencimento", "venceu", "vencido"]):
        intent, tool = "LOSSES", "get_loss_summary"
        if not allowed(PermissionCode.LOTS_VIEW, PermissionCode.REPORT_INVENTORY):
            blocked = True; answer = "Seu perfil não possui acesso às informações de perdas e validade."
        else:
            data = analytics_overview(db, user.account_id, period_start, period_end)["losses"]
            sources = ["Perdas", "Lotes"]
            answer = f"Em {period_label}, foram registradas {data['total_quantity']} unidades em perdas, equivalentes a R$ {_money(data['total_value'])} a custo. Consulte Perdas e validade para o detalhamento por motivo."
    elif any(term in text for term in ["repor", "comprar", "acabar", "ruptura", "estoque", "parado"]):
        intent, tool = "STOCK", "get_stock_risk"
        if not allowed(PermissionCode.INVENTORY_VIEW, PermissionCode.INTELLIGENCE_VIEW):
            blocked = True; answer = "Seu perfil não possui acesso às informações de estoque."
        else:
            result = generate_insights(db, user.account_id, period_start, period_end)
            sources = ["Vendas", "Estoque", "Fornecedores"]
            if "parado" in text:
                stopped = [item for item in result["insights"] if item["type"] == "PRODUTO_PARADO"]
                answer = (f"Há {len(stopped)} produto(s) sem saída além do limite configurado. " + " ".join(item["message"] for item in stopped[:5])) if stopped else "Não há produtos parados com estoque no período analisado."
            else:
                risks = [item for item in result["forecast"]["products"] if item["history_sufficient"] and item["coverage_days"] is not None and item["coverage_days"] <= 7]
                risks.sort(key=lambda item: item["coverage_days"])
                if risks:
                    details = "; ".join(f"{item['product']}: {item['coverage_days']} dias" + (f", sugestão {item['suggested_quantity']}" if item["suggested_quantity"] else "") for item in risks[:5])
                    answer = f"Com base nas vendas dos últimos {result['forecast']['period']['window_days']} dias, {len(risks)} produto(s) têm até 7 dias de cobertura. {details}. Revise prazo e fornecedor antes de criar um pedido."
                else:
                    answer = "Não há produtos com histórico suficiente e cobertura de até 7 dias no momento. Produtos com menos de 2 vendas no período não recebem previsão."
    elif any(term in text for term in ["produto mais", "mais vende", "mais importante", "categoria"]):
        intent, tool = "PRODUCTS", "get_top_products"
        if not allowed(PermissionCode.REPORT_SALES, PermissionCode.ANALYTICS_VIEW):
            blocked = True; answer = "Seu perfil não possui acesso aos relatórios de vendas."
        else:
            data = analytics_overview(db, user.account_id, period_start, period_end)
            sources = ["Vendas", "Itens vendidos"]
            top = data["products"]["top_quantity"]
            answer = (f"Por quantidade vendida em {period_label}, {top[0]['product']} liderou com {top[0]['quantity']} unidades e R$ {_money(top[0]['revenue'])} de faturamento líquido." if top else f"Não há vendas concluídas em {period_label} para formar esse ranking.")
    elif any(term in text for term in ["vendi", "vendas", "faturamento", "faturei"]):
        intent, tool = "SALES", "get_sales_summary"
        if not allowed(PermissionCode.REPORT_SALES, PermissionCode.ANALYTICS_VIEW):
            blocked = True; answer = "Seu perfil não possui acesso aos relatórios de vendas."
        else:
            sales_data = analytics_overview(db, user.account_id, period_start, period_end)
            summary = sales_data["summary"]
            sources = ["Vendas"]
            if any(term in text for term in ["caiu", "queda", "variacao"]):
                change = sales_data["comparisons"]["revenue"]
                answer = f"O faturamento variou {change:+.1f}% em relação ao período anterior equivalente. Os dados mostram a variação, mas não permitem afirmar uma causa externa." if change is not None else "Não há base anterior suficiente para calcular a variação de faturamento."
            else:
                answer = f"Em {period_label} ({period_start.strftime('%d/%m/%Y')} a {period_end.strftime('%d/%m/%Y')}), o faturamento foi R$ {_money(summary['revenue'])} em {summary['sales_count']} venda(s), com ticket médio de R$ {_money(summary['average_ticket'])}." if summary["sales_count"] else f"Não há vendas concluídas em {period_label} ({period_start.strftime('%d/%m/%Y')} a {period_end.strftime('%d/%m/%Y')})."
    else:
        answer = "Posso consultar vendas, lucro, produtos, estoque, reposição, fiado, fornecedores, perdas e validade. Tente uma das perguntas sugeridas."

    duration = int((clock.perf_counter() - started) * 1000)
    db.add(AssistantQueryLog(account_id=user.account_id, user_id=user.id, intent=intent, tool=tool, success=not blocked, duration_ms=duration))
    db.commit()
    return {"answer": answer, "intent": intent, "tool": tool, "blocked": blocked, "period": {"start": period_start.isoformat(), "end": period_end.isoformat()}, "sources": sources, "provider": "deterministic-local", "read_only": True}
