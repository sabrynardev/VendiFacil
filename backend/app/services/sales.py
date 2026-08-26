from sqlalchemy.orm import Session

from app.models.product import Product
from app.models.sale import Sale, SaleItem
from app.models.stock_movement import StockMovement, StockMovementType
from app.models.user import User
from app.schemas.sale import SaleCreate


class SaleValidationError(Exception):
    pass


def create_sale(db: Session, payload: SaleCreate, user: User) -> Sale:
    payment_method = payload.payment_method.upper()
    try:
        subtotal = 0.0
        prepared_items: list[dict] = []

        for item in payload.items:
            product = db.query(Product).filter(Product.id == item.product_id, Product.active.is_(True)).with_for_update().first()
            if not product:
                raise SaleValidationError(f"Produto {item.product_id} não encontrado.")

            current_stock = float(product.stock_quantity)
            quantity = float(item.quantity)
            if current_stock < quantity:
                raise SaleValidationError(f"Estoque insuficiente para {product.name}.")

            unit_price = float(product.sale_price)
            subtotal_item = round(unit_price * quantity - float(item.discount), 2)
            if subtotal_item < 0:
                raise SaleValidationError(f"Desconto inválido para {product.name}.")

            subtotal += subtotal_item
            prepared_items.append(
                {
                    "product": product,
                    "quantity": quantity,
                    "discount": float(item.discount),
                    "unit_price": unit_price,
                    "subtotal": subtotal_item,
                }
            )

        total = round(subtotal - float(payload.discount), 2)
        if total < 0:
            raise SaleValidationError("O desconto geral não pode gerar total negativo.")

        amount_received = float(payload.amount_received) if payload.amount_received is not None else None
        change_amount = None
        if payment_method == "DINHEIRO":
            if amount_received is None or amount_received < total:
                raise SaleValidationError("Valor recebido insuficiente para pagamento em dinheiro.")
            change_amount = round(amount_received - total, 2)

        sale = Sale(
            user_id=user.id,
            subtotal=round(subtotal, 2),
            discount=float(payload.discount),
            total=total,
            payment_method=payment_method,
            amount_received=amount_received,
            change_amount=change_amount,
        )
        db.add(sale)
        db.flush()

        for prepared_item in prepared_items:
            product = prepared_item["product"]
            previous_stock = float(product.stock_quantity)
            new_stock = round(previous_stock - prepared_item["quantity"], 2)
            product.stock_quantity = new_stock

            sale_item = SaleItem(
                sale_id=sale.id,
                product_id=product.id,
                quantity=prepared_item["quantity"],
                unit_price=prepared_item["unit_price"],
                discount=prepared_item["discount"],
                subtotal=prepared_item["subtotal"],
            )
            db.add(sale_item)

            movement = StockMovement(
                product_id=product.id,
                user_id=user.id,
                type=StockMovementType.VENDA,
                quantity=prepared_item["quantity"],
                previous_stock=previous_stock,
                new_stock=new_stock,
                reason=f"Venda #{sale.id}",
            )
            db.add(movement)

        db.commit()
        db.refresh(sale)
        return sale
    except Exception:
        db.rollback()
        raise
