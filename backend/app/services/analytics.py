import csv
import io
from collections import defaultdict
from datetime import date, datetime, time, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.core.datetime import local_period_to_utc_bounds, local_today, utc_to_local
from app.models.category import Category
from app.models.customer import Customer, CustomerDebt, CustomerPayment, DebtStatus
from app.models.financial import FinancialCategory, Payable, PayablePayment
from app.models.management_inventory import InventoryLoss, ProductLot
from app.models.product import Product
from app.models.purchase import PurchaseOrder, PurchaseReceipt, PurchaseReceiptItem, SupplierPriceHistory
from app.models.sale import PaymentMethod, Sale, SaleItem, SalePayment, SaleStatus
from app.models.supplier import Supplier
from app.services.financial import financial_summary


class AnalyticsValidationError(Exception):
    pass


def bounds(start: date, end: date) -> tuple[datetime, datetime]:
    if end < start:
        raise AnalyticsValidationError("A data final deve ser igual ou posterior à data inicial.")
    if (end - start).days > 730:
        raise AnalyticsValidationError("O período máximo para análise é de 730 dias.")
    return local_period_to_utc_bounds(start, end)


def previous_period(start: date, end: date) -> tuple[date, date]:
    duration = (end - start).days
    previous_end = start - timedelta(days=1)
    return previous_end - timedelta(days=duration), previous_end


def variation(current: float, previous: float) -> float | None:
    if previous == 0:
        return 0.0 if current == 0 else None
    return round((current - previous) / abs(previous) * 100, 2)


def _sale_items(db: Session, account_id: int, start_at: datetime, end_at: datetime):
    return db.query(SaleItem, Sale, Product, Category).join(Sale, Sale.id == SaleItem.sale_id).join(Product, Product.id == SaleItem.product_id).outerjoin(Category, Category.id == Product.category_id).filter(
        Sale.account_id == account_id,
        Sale.status == SaleStatus.COMPLETED,
        Sale.created_at.between(start_at, end_at),
    ).all()


def product_analytics(db: Session, account_id: int, start: date, end: date, stopped_days: int = 30) -> dict:
    start_at, end_at = bounds(start, end)
    products = db.query(Product).options(joinedload(Product.category)).filter(Product.account_id == account_id, Product.active.is_(True)).all()
    aggregate = {product.id: {"product_id": product.id, "product": product.name, "category": product.category.name if product.category else "Sem categoria", "quantity": 0.0, "revenue": 0.0, "cmv": 0.0, "stock": float(product.stock_quantity), "minimum_stock": float(product.minimum_stock), "unit_cost": float(product.cost_price), "sale_price": float(product.sale_price), "created_at": product.created_at} for product in products}
    for item, sale, product, category in _sale_items(db, account_id, start_at, end_at):
        row = aggregate[product.id]
        ratio = float(sale.total) / float(sale.subtotal) if float(sale.subtotal) else 0
        row["quantity"] += float(item.quantity)
        row["revenue"] += float(item.subtotal) * ratio
        row["cmv"] += float(item.cost_price) * float(item.quantity)

    rows = []
    period_days = max((end - start).days + 1, 1)
    last_sales = dict(db.query(SaleItem.product_id, func.max(Sale.created_at)).join(Sale).filter(Sale.account_id == account_id, Sale.status == SaleStatus.COMPLETED).group_by(SaleItem.product_id).all())
    cutoff = datetime.combine(end - timedelta(days=stopped_days), time.max)
    stopped = []
    for row in aggregate.values():
        row["revenue"] = round(row["revenue"], 2)
        row["cmv"] = round(row["cmv"], 2)
        row["profit"] = round(row["revenue"] - row["cmv"], 2)
        row["margin"] = round(row["profit"] / row["revenue"] * 100, 2) if row["revenue"] else 0
        row["average_daily_sales"] = round(row["quantity"] / period_days, 3)
        row["coverage_days"] = round(row["stock"] / row["average_daily_sales"], 1) if row["average_daily_sales"] > 0 else None
        row["stock_cost_value"] = round(row["stock"] * row["unit_cost"], 2)
        row["potential_sale_value"] = round(row["stock"] * row["sale_price"], 2)
        last_sale = last_sales.get(row["product_id"])
        row["last_sale_at"] = last_sale.isoformat() if last_sale else None
        rows.append(row)
        eligible_since = last_sale or row["created_at"]
        if row["stock"] > 0 and eligible_since <= cutoff:
            days_without_sale = (end - eligible_since.date()).days
            stopped.append({**row, "days_without_sale": max(days_without_sale, 0), "stopped_value": row["stock_cost_value"]})

    sold = [row for row in rows if row["quantity"] > 0]
    by_quantity = sorted(sold, key=lambda row: (-row["quantity"], row["product"]))
    by_revenue = sorted(sold, key=lambda row: (-row["revenue"], row["product"]))
    by_profit = sorted(sold, key=lambda row: (-row["profit"], row["product"]))
    least_sold = sorted(sold, key=lambda row: (row["quantity"], row["product"]))

    total_revenue = sum(row["revenue"] for row in by_revenue)
    cumulative = 0.0
    abc = []
    for row in by_revenue:
        percentage = row["revenue"] / total_revenue * 100 if total_revenue else 0
        before = cumulative
        cumulative += percentage
        classification = "A" if before < 80 else "B" if before < 95 else "C"
        abc.append({"product_id": row["product_id"], "product": row["product"], "revenue": row["revenue"], "percentage": round(percentage, 2), "cumulative_percentage": round(cumulative, 2), "class": classification})

    category_rows = defaultdict(lambda: {"quantity": 0.0, "revenue": 0.0, "cmv": 0.0})
    for row in sold:
        target = category_rows[row["category"]]
        target["quantity"] += row["quantity"]
        target["revenue"] += row["revenue"]
        target["cmv"] += row["cmv"]
    categories = []
    for name, values in category_rows.items():
        profit = values["revenue"] - values["cmv"]
        categories.append({"category": name, "quantity": round(values["quantity"], 3), "revenue": round(values["revenue"], 2), "cmv": round(values["cmv"], 2), "profit": round(profit, 2), "margin": round(profit / values["revenue"] * 100, 2) if values["revenue"] else 0, "participation": round(values["revenue"] / total_revenue * 100, 2) if total_revenue else 0})
    categories.sort(key=lambda row: row["revenue"], reverse=True)

    inventory_cost = round(sum(row["stock_cost_value"] for row in rows), 2)
    potential_sale = round(sum(row["potential_sale_value"] for row in rows), 2)
    cmv = round(sum(row["cmv"] for row in rows), 2)
    low_stock = [row for row in rows if row["stock"] <= row["minimum_stock"]]
    excessive = [row for row in rows if row["coverage_days"] is not None and row["coverage_days"] >= 90]
    return {
        "products": rows,
        "top_quantity": by_quantity[:20],
        "top_revenue": by_revenue[:20],
        "top_profit": by_profit[:20],
        "least_sold": least_sold[:20],
        "stopped": sorted(stopped, key=lambda row: (-row["stopped_value"], row["product"])),
        "abc": abc,
        "categories": categories,
        "inventory": {"cost_value": inventory_cost, "potential_sale_value": potential_sale, "turnover_simplified": round(cmv / inventory_cost, 3) if inventory_cost else None, "low_stock": low_stock, "excessive_stock": excessive},
    }


def sales_analytics(db: Session, account_id: int, start: date, end: date) -> dict:
    start_at, end_at = bounds(start, end)
    sales = db.query(Sale).filter(Sale.account_id == account_id, Sale.status == SaleStatus.COMPLETED, Sale.created_at.between(start_at, end_at)).all()
    timeline_map = defaultdict(lambda: {"revenue": 0.0, "sales_count": 0})
    hourly = defaultdict(lambda: {"revenue": 0.0, "sales_count": 0})
    for sale in sales:
        local_created_at = utc_to_local(sale.created_at)
        day = local_created_at.date().isoformat()
        timeline_map[day]["revenue"] += float(sale.total)
        timeline_map[day]["sales_count"] += 1
        hour = local_created_at.hour
        hourly[hour]["revenue"] += float(sale.total)
        hourly[hour]["sales_count"] += 1
    timeline = []
    current = start
    while current <= end:
        values = timeline_map[current.isoformat()]
        timeline.append({"date": current.isoformat(), "revenue": round(values["revenue"], 2), "sales_count": values["sales_count"]})
        current += timedelta(days=1)
    hours = [{"hour": hour, "label": f"{hour:02d}h–{hour + 1:02d}h", "revenue": round(values["revenue"], 2), "sales_count": values["sales_count"]} for hour, values in sorted(hourly.items())]
    payments = db.query(SalePayment.method, func.coalesce(func.sum(SalePayment.amount), 0)).join(Sale).filter(Sale.account_id == account_id, Sale.status == SaleStatus.COMPLETED, Sale.created_at.between(start_at, end_at)).group_by(SalePayment.method).all()
    total_payments = sum(float(total) for _, total in payments)
    payment_methods = [{"method": method.value if hasattr(method, "value") else str(method), "amount": round(float(total), 2), "participation": round(float(total) / total_payments * 100, 2) if total_payments else 0} for method, total in payments]
    return {"timeline": timeline, "hours": hours, "payment_methods": sorted(payment_methods, key=lambda row: row["amount"], reverse=True)}


def credit_analytics(db: Session, account_id: int, start: date, end: date) -> dict:
    start_at, end_at = bounds(start, end)
    debts = db.query(CustomerDebt).options(joinedload(CustomerDebt.customer)).filter(CustomerDebt.account_id == account_id, CustomerDebt.status.in_([DebtStatus.OPEN, DebtStatus.PARTIAL])).all()
    today = local_today()
    buckets = {"NAO_VENCIDO": 0.0, "1_7_DIAS": 0.0, "8_30_DIAS": 0.0, "31_60_DIAS": 0.0, "ACIMA_60_DIAS": 0.0}
    customers = defaultdict(float)
    age_weight = 0.0
    total = 0.0
    overdue = 0.0
    for debt in debts:
        balance = float(debt.balance)
        total += balance
        customers[(debt.customer_id, debt.customer.name)] += balance
        age_weight += (today - utc_to_local(debt.created_at).date()).days * balance
        overdue_days = (today - debt.due_date).days if debt.due_date and debt.due_date < today else 0
        if overdue_days <= 0: buckets["NAO_VENCIDO"] += balance
        elif overdue_days <= 7: buckets["1_7_DIAS"] += balance
        elif overdue_days <= 30: buckets["8_30_DIAS"] += balance
        elif overdue_days <= 60: buckets["31_60_DIAS"] += balance
        else: buckets["ACIMA_60_DIAS"] += balance
        if overdue_days > 0: overdue += balance
    receipts = float(db.query(func.coalesce(func.sum(CustomerPayment.amount), 0)).filter(CustomerPayment.account_id == account_id, CustomerPayment.created_at.between(start_at, end_at)).scalar() or 0)
    ranking = [{"customer_id": key[0], "customer": key[1], "balance": round(value, 2)} for key, value in sorted(customers.items(), key=lambda item: item[1], reverse=True)]
    return {"open_total": round(total, 2), "overdue_total": round(overdue, 2), "debtor_count": len(customers), "largest_debt": ranking[0]["balance"] if ranking else 0, "average_age_days": round(age_weight / total, 1) if total else 0, "receipts": round(receipts, 2), "aging_buckets": [{"bucket": key, "amount": round(value, 2)} for key, value in buckets.items()], "top_debtors": ranking[:20]}


def customer_analytics(db: Session, account_id: int, start: date, end: date) -> list[dict]:
    start_at, end_at = bounds(start, end)
    rows = db.query(Sale.customer_id, func.count(Sale.id), func.sum(Sale.total), func.max(Sale.created_at)).filter(Sale.account_id == account_id, Sale.customer_id.is_not(None), Sale.status == SaleStatus.COMPLETED, Sale.created_at.between(start_at, end_at)).group_by(Sale.customer_id).all()
    names = {customer.id: customer.name for customer in db.query(Customer).filter(Customer.account_id == account_id).all()}
    return sorted([{"customer_id": customer_id, "customer": names.get(customer_id, "Cliente"), "purchases": count, "revenue": round(float(total), 2), "average_ticket": round(float(total) / count, 2), "last_purchase_at": last.isoformat()} for customer_id, count, total, last in rows], key=lambda row: row["revenue"], reverse=True)


def loss_and_expiry_analytics(db: Session, account_id: int, start: date, end: date, gross_profit: float) -> dict:
    start_at, end_at = bounds(start, end)
    losses = db.query(InventoryLoss).options(joinedload(InventoryLoss.product), joinedload(InventoryLoss.lot)).filter(InventoryLoss.account_id == account_id, InventoryLoss.created_at.between(start_at, end_at)).all()
    by_reason = defaultdict(lambda: {"quantity": 0.0, "value": 0.0})
    products = defaultdict(lambda: {"quantity": 0.0, "value": 0.0})
    total_value = 0.0
    total_quantity = 0.0
    for loss in losses:
        cost = float(loss.unit_cost)
        value = float(loss.quantity) * cost
        reason = loss.reason.value if hasattr(loss.reason, "value") else str(loss.reason)
        by_reason[reason]["quantity"] += float(loss.quantity); by_reason[reason]["value"] += value
        products[loss.product.name]["quantity"] += float(loss.quantity); products[loss.product.name]["value"] += value
        total_value += value; total_quantity += float(loss.quantity)
    today = local_today()
    lots = db.query(ProductLot).options(joinedload(ProductLot.product)).filter(ProductLot.account_id == account_id, ProductLot.current_quantity > 0, ProductLot.expiration_date.is_not(None)).all()
    expiry = {"VENCIDO": {"quantity": 0.0, "value": 0.0}, "ATE_3_DIAS": {"quantity": 0.0, "value": 0.0}, "ATE_7_DIAS": {"quantity": 0.0, "value": 0.0}, "ATE_30_DIAS": {"quantity": 0.0, "value": 0.0}}
    for lot in lots:
        days = (lot.expiration_date - today).days
        key = "VENCIDO" if days < 0 else "ATE_3_DIAS" if days <= 3 else "ATE_7_DIAS" if days <= 7 else "ATE_30_DIAS" if days <= 30 else None
        if key:
            expiry[key]["quantity"] += float(lot.current_quantity); expiry[key]["value"] += float(lot.current_quantity) * float(lot.unit_cost)
    return {"total_value": round(total_value, 2), "total_quantity": round(total_quantity, 3), "impact_on_gross_profit": round(total_value / gross_profit * 100, 2) if gross_profit > 0 else None, "by_reason": [{"reason": key, "quantity": round(value["quantity"], 3), "value": round(value["value"], 2)} for key, value in by_reason.items()], "products": [{"product": key, "quantity": round(value["quantity"], 3), "value": round(value["value"], 2)} for key, value in sorted(products.items(), key=lambda item: item[1]["value"], reverse=True)], "expiry_risk": [{"range": key, "quantity": round(value["quantity"], 3), "value": round(value["value"], 2)} for key, value in expiry.items()]}


def supplier_analytics(db: Session, account_id: int, start: date, end: date) -> dict:
    start_at, end_at = bounds(start, end)
    suppliers = {item.id: item.name for item in db.query(Supplier).filter(Supplier.account_id == account_id).all()}
    totals = defaultdict(lambda: {"total": 0.0, "orders": set(), "products": set(), "last_purchase_at": None})
    receipt_rows = db.query(PurchaseReceiptItem, PurchaseReceipt, PurchaseOrder).join(PurchaseReceipt, PurchaseReceipt.id == PurchaseReceiptItem.receipt_id).join(PurchaseOrder, PurchaseOrder.id == PurchaseReceipt.order_id).filter(PurchaseReceipt.account_id == account_id, PurchaseReceipt.received_at.between(start_at, end_at)).all()
    for item, receipt, order in receipt_rows:
        row = totals[order.supplier_id]; row["total"] += float(item.quantity) * float(item.unit_cost); row["orders"].add(order.id); row["products"].add(item.order_item.product_id); row["last_purchase_at"] = max(row["last_purchase_at"] or receipt.received_at, receipt.received_at)
    ranking = [{"supplier_id": supplier_id, "supplier": suppliers.get(supplier_id, "Fornecedor"), "total_purchased": round(values["total"], 2), "orders": len(values["orders"]), "products": len(values["products"]), "last_purchase_at": values["last_purchase_at"].isoformat() if values["last_purchase_at"] else None} for supplier_id, values in totals.items()]
    ranking.sort(key=lambda row: row["total_purchased"], reverse=True)
    total_purchases = sum(row["total_purchased"] for row in ranking)
    for row in ranking: row["concentration"] = round(row["total_purchased"] / total_purchases * 100, 2) if total_purchases else 0

    histories = db.query(SupplierPriceHistory).options(joinedload(SupplierPriceHistory.product), joinedload(SupplierPriceHistory.supplier)).filter(SupplierPriceHistory.account_id == account_id, SupplierPriceHistory.recorded_at.between(start_at, end_at)).order_by(SupplierPriceHistory.recorded_at).all()
    grouped = defaultdict(list)
    latest = {}
    for item in histories:
        grouped[(item.product_id, item.supplier_id)].append(item)
        latest[(item.product_id, item.supplier_id)] = item
    increases = []
    for items in grouped.values():
        first, last = items[0], items[-1]
        change = (float(last.unit_cost) - float(first.unit_cost)) / float(first.unit_cost) * 100 if float(first.unit_cost) else 0
        increases.append({"product_id": last.product_id, "product": last.product.name, "supplier_id": last.supplier_id, "supplier": last.supplier.name, "first_cost": float(first.unit_cost), "last_cost": float(last.unit_cost), "variation": round(change, 2), "records": [{"date": item.recorded_at.date().isoformat(), "cost": float(item.unit_cost)} for item in items]})
    increases.sort(key=lambda row: row["variation"], reverse=True)
    comparisons = defaultdict(list)
    for item in latest.values(): comparisons[(item.product_id, item.product.name)].append({"supplier": item.supplier.name, "cost": float(item.unit_cost), "recorded_at": item.recorded_at.isoformat()})
    return {"ranking": ranking, "cost_changes": increases, "comparisons": [{"product_id": key[0], "product": key[1], "suppliers": values} for key, values in comparisons.items() if len(values) > 1]}


def expense_analytics(db: Session, account_id: int, start: date, end: date) -> list[dict]:
    start_at, end_at = bounds(start, end)
    rows = db.query(FinancialCategory.name, Payable.affects_result, func.sum(PayablePayment.amount)).join(Payable, Payable.category_id == FinancialCategory.id).join(PayablePayment, PayablePayment.payable_id == Payable.id).filter(Payable.account_id == account_id, PayablePayment.payment_date.between(start_at, end_at)).group_by(FinancialCategory.name, Payable.affects_result).all()
    return sorted([{"category": name, "type": "OPERACIONAL" if affects_result else "MERCADORIA", "amount": round(float(total), 2)} for name, affects_result, total in rows], key=lambda row: row["amount"], reverse=True)


def analytics_overview(db: Session, account_id: int, start: date, end: date, stopped_days: int = 30) -> dict:
    bounds(start, end)
    previous_start, previous_end = previous_period(start, end)
    current_summary = financial_summary(db, account_id, start, end)
    previous_summary = financial_summary(db, account_id, previous_start, previous_end)
    comparisons = {key: variation(current_summary[key], previous_summary[key]) for key in ["revenue", "cmv", "gross_profit", "gross_margin", "operational_expenses", "estimated_result", "sales_count", "average_ticket"]}
    products = product_analytics(db, account_id, start, end, stopped_days)
    sales = sales_analytics(db, account_id, start, end)
    credit = credit_analytics(db, account_id, start, end)
    losses = loss_and_expiry_analytics(db, account_id, start, end, current_summary["gross_profit"])
    return {"period": {"start": start.isoformat(), "end": end.isoformat(), "previous_start": previous_start.isoformat(), "previous_end": previous_end.isoformat()}, "summary": current_summary, "comparisons": comparisons, "sales": sales, "products": products, "credit": credit, "customers": customer_analytics(db, account_id, start, end), "losses": losses, "suppliers": supplier_analytics(db, account_id, start, end), "expenses": expense_analytics(db, account_id, start, end)}


def export_csv(data: dict, report: str) -> tuple[str, str]:
    definitions = {
        "products": (data["products"]["products"], [("Produto", "product"), ("Categoria", "category"), ("Quantidade Vendida", "quantity"), ("Faturamento", "revenue"), ("CMV", "cmv"), ("Lucro Bruto", "profit"), ("Margem (%)", "margin"), ("Estoque Atual", "stock")]),
        "abc": (data["products"]["abc"], [("Produto", "product"), ("Faturamento", "revenue"), ("Participação (%)", "percentage"), ("Acumulado (%)", "cumulative_percentage"), ("Classe", "class")]),
        "stopped": (data["products"]["stopped"], [("Produto", "product"), ("Dias sem Venda", "days_without_sale"), ("Estoque", "stock"), ("Custo Unitário", "unit_cost"), ("Valor Parado", "stopped_value")]),
        "suppliers": (data["suppliers"]["ranking"], [("Fornecedor", "supplier"), ("Total Comprado", "total_purchased"), ("Pedidos", "orders"), ("Produtos", "products"), ("Concentração (%)", "concentration")]),
        "losses": (data["losses"]["products"], [("Produto", "product"), ("Quantidade", "quantity"), ("Valor Perdido", "value")]),
    }
    if report not in definitions:
        raise AnalyticsValidationError("Relatório inválido para exportação.")
    rows, columns = definitions[report]
    output = io.StringIO(); writer = csv.writer(output, delimiter=";"); writer.writerow([label for label, _ in columns])
    for row in rows: writer.writerow([row.get(key, "") for _, key in columns])
    return f"vendi-{report}.csv", "\ufeff" + output.getvalue()
