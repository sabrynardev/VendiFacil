from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine


def _has_column(inspector, table_name: str, column_name: str) -> bool:
    return any(column["name"] == column_name for column in inspector.get_columns(table_name))


def ensure_multitenant_schema(engine: Engine) -> None:
    if engine.dialect.name != "sqlite":
        return

    with engine.begin() as connection:
        inspector = inspect(connection)

        if "accounts" not in inspector.get_table_names():
            connection.execute(
                text(
                    """
                    CREATE TABLE accounts (
                        id INTEGER PRIMARY KEY,
                        name VARCHAR(160) NOT NULL UNIQUE,
                        active BOOLEAN NOT NULL DEFAULT 1,
                        created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                    )
                    """
                )
            )
            connection.execute(text("CREATE INDEX IF NOT EXISTS ix_accounts_id ON accounts (id)"))
            inspector = inspect(connection)

        demo_account_id = connection.execute(text("SELECT id FROM accounts WHERE name = 'Demo Principal' LIMIT 1")).scalar()
        if demo_account_id is None:
            connection.execute(
                text(
                    """
                    INSERT INTO accounts (name, active, created_at)
                    VALUES ('Demo Principal', 1, CURRENT_TIMESTAMP)
                    """
                )
            )
            demo_account_id = connection.execute(text("SELECT id FROM accounts WHERE name = 'Demo Principal' LIMIT 1")).scalar_one()

        simple_tables = ["users", "suppliers", "sales", "stock_movements"]
        for table_name in simple_tables:
            if table_name in inspector.get_table_names() and not _has_column(inspector, table_name, "account_id"):
                connection.execute(text(f"ALTER TABLE {table_name} ADD COLUMN account_id INTEGER"))

        inspector = inspect(connection)
        if "users" in inspector.get_table_names() and not _has_column(inspector, "users", "profile_id"):
            connection.execute(text("ALTER TABLE users ADD COLUMN profile_id INTEGER"))
        if "products" in inspector.get_table_names() and not _has_column(inspector, "products", "brand"):
            connection.execute(text("ALTER TABLE products ADD COLUMN brand VARCHAR(100)"))
        if "suppliers" in inspector.get_table_names() and not _has_column(inspector, "suppliers", "active"):
            connection.execute(text("ALTER TABLE suppliers ADD COLUMN active BOOLEAN NOT NULL DEFAULT 1"))

        inspector = inspect(connection)

        if "categories" in inspector.get_table_names() and not _has_column(inspector, "categories", "account_id"):
            connection.execute(text("PRAGMA foreign_keys=OFF"))
            connection.execute(
                text(
                    """
                    CREATE TABLE categories_new (
                        id INTEGER PRIMARY KEY,
                        account_id INTEGER NOT NULL,
                        name VARCHAR(100) NOT NULL,
                        description TEXT,
                        created_at DATETIME NOT NULL,
                        FOREIGN KEY(account_id) REFERENCES accounts(id)
                    )
                    """
                )
            )
            connection.execute(
                text(
                    """
                    INSERT INTO categories_new (id, account_id, name, description, created_at)
                    SELECT id, :account_id, name, description, created_at
                    FROM categories
                    """
                ),
                {"account_id": demo_account_id},
            )
            connection.execute(text("DROP TABLE categories"))
            connection.execute(text("ALTER TABLE categories_new RENAME TO categories"))
            connection.execute(text("CREATE INDEX IF NOT EXISTS ix_categories_id ON categories (id)"))
            connection.execute(
                text("CREATE UNIQUE INDEX IF NOT EXISTS uq_categories_account_name ON categories (account_id, name)")
            )
            connection.execute(text("PRAGMA foreign_keys=ON"))
            inspector = inspect(connection)

        if "products" in inspector.get_table_names() and not _has_column(inspector, "products", "account_id"):
            connection.execute(text("PRAGMA foreign_keys=OFF"))
            connection.execute(
                text(
                    """
                    CREATE TABLE products_new (
                        id INTEGER PRIMARY KEY,
                        account_id INTEGER NOT NULL,
                        name VARCHAR(160) NOT NULL,
                        brand VARCHAR(100),
                        description TEXT,
                        sku VARCHAR(60) NOT NULL,
                        barcode VARCHAR(60),
                        category_id INTEGER,
                        supplier_id INTEGER,
                        cost_price NUMERIC(10, 2) NOT NULL,
                        sale_price NUMERIC(10, 2) NOT NULL,
                        stock_quantity NUMERIC(10, 2) NOT NULL,
                        minimum_stock NUMERIC(10, 2) NOT NULL,
                        unit VARCHAR(30) NOT NULL,
                        active BOOLEAN NOT NULL,
                        created_at DATETIME NOT NULL,
                        updated_at DATETIME NOT NULL,
                        FOREIGN KEY(account_id) REFERENCES accounts(id),
                        FOREIGN KEY(category_id) REFERENCES categories(id),
                        FOREIGN KEY(supplier_id) REFERENCES suppliers(id)
                    )
                    """
                )
            )
            connection.execute(
                text(
                    """
                    INSERT INTO products_new (
                        id, account_id, name, brand, description, sku, barcode, category_id, supplier_id,
                        cost_price, sale_price, stock_quantity, minimum_stock, unit, active, created_at, updated_at
                    )
                    SELECT
                        id, :account_id, name, brand, description, sku, barcode, category_id, supplier_id,
                        cost_price, sale_price, stock_quantity, minimum_stock, unit, active, created_at, updated_at
                    FROM products
                    """
                ),
                {"account_id": demo_account_id},
            )
            connection.execute(text("DROP TABLE products"))
            connection.execute(text("ALTER TABLE products_new RENAME TO products"))
            connection.execute(text("CREATE INDEX IF NOT EXISTS ix_products_id ON products (id)"))
            connection.execute(text("CREATE INDEX IF NOT EXISTS ix_products_sku ON products (sku)"))
            connection.execute(text("CREATE INDEX IF NOT EXISTS ix_products_barcode ON products (barcode)"))
            connection.execute(
                text("CREATE UNIQUE INDEX IF NOT EXISTS uq_products_account_sku ON products (account_id, sku)")
            )
            connection.execute(
                text(
                    "CREATE UNIQUE INDEX IF NOT EXISTS uq_products_account_barcode ON products (account_id, barcode) WHERE barcode IS NOT NULL"
                )
            )
            connection.execute(text("PRAGMA foreign_keys=ON"))
            inspector = inspect(connection)

        updates = [
            ("users", "UPDATE users SET account_id = :account_id WHERE account_id IS NULL"),
            ("suppliers", "UPDATE suppliers SET account_id = :account_id WHERE account_id IS NULL"),
            ("sales", "UPDATE sales SET account_id = :account_id WHERE account_id IS NULL"),
            ("stock_movements", "UPDATE stock_movements SET account_id = :account_id WHERE account_id IS NULL"),
        ]
        for table_name, statement in updates:
            if table_name in inspector.get_table_names() and _has_column(inspector, table_name, "account_id"):
                connection.execute(text(statement), {"account_id": demo_account_id})

        if "suppliers" in inspector.get_table_names():
            connection.execute(text("CREATE INDEX IF NOT EXISTS ix_suppliers_account_id ON suppliers (account_id)"))
        if "categories" in inspector.get_table_names():
            connection.execute(text("CREATE INDEX IF NOT EXISTS ix_categories_account_id ON categories (account_id)"))
            connection.execute(
                text("CREATE UNIQUE INDEX IF NOT EXISTS uq_categories_account_name ON categories (account_id, name)")
            )
        if "products" in inspector.get_table_names():
            connection.execute(text("CREATE INDEX IF NOT EXISTS ix_products_account_id ON products (account_id)"))
            connection.execute(
                text("CREATE UNIQUE INDEX IF NOT EXISTS uq_products_account_sku ON products (account_id, sku)")
            )
            connection.execute(
                text(
                    "CREATE UNIQUE INDEX IF NOT EXISTS uq_products_account_barcode ON products (account_id, barcode) WHERE barcode IS NOT NULL"
                )
            )
        if "sales" in inspector.get_table_names():
            connection.execute(text("CREATE INDEX IF NOT EXISTS ix_sales_account_id ON sales (account_id)"))
        if "stock_movements" in inspector.get_table_names():
            connection.execute(text("CREATE INDEX IF NOT EXISTS ix_stock_movements_account_id ON stock_movements (account_id)"))
        if "users" in inspector.get_table_names():
            connection.execute(text("CREATE INDEX IF NOT EXISTS ix_users_account_id ON users (account_id)"))
            connection.execute(text("CREATE INDEX IF NOT EXISTS ix_users_profile_id ON users (profile_id)"))
        if "profiles" in inspector.get_table_names():
            connection.execute(text("CREATE INDEX IF NOT EXISTS ix_profiles_account_id ON profiles (account_id)"))
            connection.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS uq_profiles_account_code ON profiles (account_id, code)"))
