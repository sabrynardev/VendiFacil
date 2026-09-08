from datetime import datetime, timedelta
from random import choice, randint, uniform

from sqlalchemy.orm import Session

from app.auth.security import hash_password
from app.core.config import get_settings
from app.models.account import Account
from app.models.category import Category
from app.models.product import Product
from app.models.sale import Sale, SaleItem
from app.models.stock_movement import StockMovement, StockMovementType
from app.models.supplier import Supplier
from app.models.user import User, UserRole
from app.services.accounts import ensure_default_categories
from app.services.profiles import ensure_default_profiles


def seed_database(db: Session):
    settings = get_settings()

    demo_account = db.query(Account).filter(Account.name == "Demo Principal").first()
    if not demo_account:
        demo_account = Account(name="Demo Principal", active=True)
        db.add(demo_account)
        db.commit()
        db.refresh(demo_account)

    profiles = ensure_default_profiles(db, demo_account.id)

    admin = db.query(User).filter(User.email == settings.seed_admin_email).first()
    if not admin:
        admin = User(
            account_id=demo_account.id,
            profile_id=profiles[UserRole.ADMIN.value].id,
            name="Administrador",
            email=settings.seed_admin_email,
            password_hash=hash_password(settings.seed_admin_password),
            role=UserRole.ADMIN,
            active=True,
        )
        db.add(admin)

    cashier = db.query(User).filter(User.email == "sabrina@marketpulse.dev").first()
    if not cashier:
        cashier = User(
            account_id=demo_account.id,
            profile_id=profiles[UserRole.CAIXA.value].id,
            name="Sabrina",
            email="sabrina@marketpulse.dev",
            password_hash=hash_password("caixa123"),
            role=UserRole.CAIXA,
            active=True,
        )
        db.add(cashier)

    for user in db.query(User).filter(User.account_id == demo_account.id, User.profile_id.is_(None)).all():
        user.profile_id = profiles[user.role.value].id

    db.commit()
    db.refresh(demo_account)
    cashier = db.query(User).filter(User.email == "sabrina@marketpulse.dev").first()

    ensure_default_categories(db, demo_account.id)

    suppliers_seed = [
        {"name": "Distribuidora Centro", "phone": "(11) 3333-1111", "email": "contato@centro.local"},
        {"name": "Atacado Bom Preco", "phone": "(11) 3333-2222", "email": "compras@bompreco.local"},
    ]
    for supplier_data in suppliers_seed:
        exists = (
            db.query(Supplier)
            .filter(Supplier.account_id == demo_account.id, Supplier.name == supplier_data["name"])
            .first()
        )
        if not exists:
            db.add(Supplier(account_id=demo_account.id, **supplier_data))

    db.commit()

    category_map = {
        category.name: category
        for category in db.query(Category).filter(Category.account_id == demo_account.id).all()
    }
    supplier_list = db.query(Supplier).filter(Supplier.account_id == demo_account.id).all()

    products_seed = [
        ("Coca-Cola 2L", "Bebidas", 6.20, 9.50, 40, 20, "7894900011517"),
        ("Arroz 5kg", "Alimentos", 22.40, 28.90, 24, 12, "7896006716111"),
        ("Feijao 1kg", "Alimentos", 6.30, 8.90, 14, 10, "7891025301512"),
        ("Leite Integral 1L", "Bebidas", 4.10, 5.49, 18, 12, "7894900701515"),
        ("Cafe 500g", "Alimentos", 13.50, 18.90, 10, 8, "7891910000197"),
        ("Acucar 1kg", "Alimentos", 3.10, 4.89, 30, 15, "7896089001012"),
        ("Detergente", "Limpeza", 1.80, 2.99, 50, 20, "7896098901012"),
        ("Sabonete", "Higiene", 2.30, 3.49, 36, 18, "7896004402211"),
        ("Biscoito", "Doces", 3.10, 4.79, 42, 20, "7896051111210"),
        ("Agua Mineral", "Bebidas", 1.20, 2.50, 60, 25, "7890000100100"),
    ]

    for index, item in enumerate(products_seed, start=1):
        name, category_name, cost_price, sale_price, stock, minimum_stock, barcode = item
        sku = f"SKU-{index:04d}"
        exists = db.query(Product).filter(Product.account_id == demo_account.id, Product.sku == sku).first()
        if not exists:
            db.add(
                Product(
                    account_id=demo_account.id,
                    name=name,
                    description=f"{name} para o PDV VendiFácil",
                    sku=sku,
                    barcode=barcode,
                    category_id=category_map[category_name].id,
                    supplier_id=choice(supplier_list).id if supplier_list else None,
                    cost_price=cost_price,
                    sale_price=sale_price,
                    stock_quantity=stock,
                    minimum_stock=minimum_stock,
                    unit="UN",
                    active=True,
                )
            )

    db.commit()

    existing_demo_sales = db.query(Sale).filter(Sale.account_id == demo_account.id).count()
    if existing_demo_sales > 0 or cashier is None:
        return

    products = db.query(Product).filter(Product.account_id == demo_account.id).all()
    payment_methods = ["PIX", "DINHEIRO", "DEBITO", "CREDITO"]

    for day_offset in range(1, 15):
        sale_count = randint(3, 9)
        for _ in range(sale_count):
            created_at = datetime.utcnow() - timedelta(days=day_offset, hours=randint(1, 10), minutes=randint(0, 59))
            items = []
            subtotal = 0.0

            for _item_index in range(randint(1, 4)):
                product = choice(products)
                quantity = randint(1, 3)
                item_subtotal = round(float(product.sale_price) * quantity, 2)
                items.append((product, quantity, item_subtotal))
                subtotal += item_subtotal

            discount = round(uniform(0, min(subtotal * 0.08, 5)), 2)
            total = round(subtotal - discount, 2)
            payment_method = choice(payment_methods)
            amount_received = total if payment_method != "DINHEIRO" else round(total + uniform(0, 20), 2)
            change_amount = round(amount_received - total, 2) if payment_method == "DINHEIRO" else 0

            sale = Sale(
                account_id=demo_account.id,
                user_id=cashier.id,
                subtotal=subtotal,
                discount=discount,
                total=total,
                payment_method=payment_method,
                amount_received=amount_received,
                change_amount=change_amount,
                created_at=created_at,
            )
            db.add(sale)
            db.flush()

            for product, quantity, item_subtotal in items:
                db.add(
                    SaleItem(
                        sale_id=sale.id,
                        product_id=product.id,
                        quantity=quantity,
                        unit_price=product.sale_price,
                        discount=0,
                        subtotal=item_subtotal,
                    )
                )
                previous_stock = float(product.stock_quantity)
                product.stock_quantity = max(round(previous_stock - quantity, 2), 0)
                db.add(
                    StockMovement(
                        account_id=demo_account.id,
                        product_id=product.id,
                        user_id=cashier.id,
                        type=StockMovementType.VENDA,
                        quantity=quantity,
                        previous_stock=previous_stock,
                        new_stock=float(product.stock_quantity),
                        reason=f"Venda historica #{sale.id}",
                        created_at=created_at,
                    )
                )

    db.commit()
