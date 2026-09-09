from enum import StrEnum


class PermissionCode(StrEnum):
    DASHBOARD_VIEW = "dashboard.view"
    CASHIER_OPERATE = "cashier.operate"
    CASH_REGISTER_VIEW = "cash_register.view"
    CASH_REGISTER_OPERATE = "cash_register.operate"
    CASH_REGISTER_MANAGE = "cash_register.manage"
    DISCOUNT_NORMAL = "discount.normal"
    DISCOUNT_SPECIAL = "discount.special"
    PRODUCTS_VIEW = "products.view"
    PRODUCTS_MANAGE = "products.manage"
    INVENTORY_VIEW = "inventory.view"
    INVENTORY_MANAGE = "inventory.manage"
    SALES_VIEW = "sales.view"
    SALES_CANCEL = "sales.cancel"
    SUPPLIERS_VIEW = "suppliers.view"
    SUPPLIERS_MANAGE = "suppliers.manage"
    PURCHASES_VIEW = "purchases.view"
    PURCHASES_MANAGE = "purchases.manage"
    LOTS_VIEW = "lots.view"
    LOTS_MANAGE = "lots.manage"
    INVENTORY_COUNT = "inventory.count"
    CUSTOMERS_VIEW = "customers.view"
    CUSTOMERS_MANAGE = "customers.manage"
    CREDIT_SELL = "credit.sell"
    CREDIT_RECEIVE = "credit.receive"
    CREDIT_MANAGE = "credit.manage"
    REPORTS_VIEW = "reports.view"
    PROFIT_VIEW = "profit.view"
    USERS_MANAGE = "users.manage"
    AUDIT_VIEW = "audit.view"
    SETTINGS_VIEW = "settings.view"


PERMISSION_LABELS = {
    PermissionCode.DASHBOARD_VIEW: ("Visualizar dashboard", "Geral"),
    PermissionCode.CASHIER_OPERATE: ("Operar PDV", "Caixa"),
    PermissionCode.CASH_REGISTER_VIEW: ("Visualizar caixas", "Caixa"),
    PermissionCode.CASH_REGISTER_OPERATE: ("Abrir e fechar o próprio caixa", "Caixa"),
    PermissionCode.CASH_REGISTER_MANAGE: ("Registrar sangria e suprimento", "Caixa"),
    PermissionCode.DISCOUNT_NORMAL: ("Aplicar desconto até 10%", "Vendas"),
    PermissionCode.DISCOUNT_SPECIAL: ("Autorizar desconto especial", "Vendas"),
    PermissionCode.PRODUCTS_VIEW: ("Visualizar produtos", "Produtos"),
    PermissionCode.PRODUCTS_MANAGE: ("Gerenciar produtos", "Produtos"),
    PermissionCode.INVENTORY_VIEW: ("Visualizar estoque", "Estoque"),
    PermissionCode.INVENTORY_MANAGE: ("Movimentar estoque", "Estoque"),
    PermissionCode.SALES_VIEW: ("Visualizar vendas", "Vendas"),
    PermissionCode.SALES_CANCEL: ("Cancelar vendas", "Vendas"),
    PermissionCode.SUPPLIERS_VIEW: ("Visualizar fornecedores", "Fornecedores"),
    PermissionCode.SUPPLIERS_MANAGE: ("Gerenciar fornecedores", "Fornecedores"),
    PermissionCode.PURCHASES_VIEW: ("Visualizar compras", "Compras"),
    PermissionCode.PURCHASES_MANAGE: ("Gerenciar compras e recebimentos", "Compras"),
    PermissionCode.LOTS_VIEW: ("Visualizar lotes e validade", "Estoque"),
    PermissionCode.LOTS_MANAGE: ("Gerenciar lotes e perdas", "Estoque"),
    PermissionCode.INVENTORY_COUNT: ("Realizar inventários", "Estoque"),
    PermissionCode.CUSTOMERS_VIEW: ("Visualizar clientes", "Clientes"),
    PermissionCode.CUSTOMERS_MANAGE: ("Gerenciar clientes", "Clientes"),
    PermissionCode.CREDIT_SELL: ("Realizar venda fiada", "Clientes"),
    PermissionCode.CREDIT_RECEIVE: ("Receber pagamento de fiado", "Clientes"),
    PermissionCode.CREDIT_MANAGE: ("Gerenciar limites e autorizações", "Clientes"),
    PermissionCode.REPORTS_VIEW: ("Visualizar relatórios", "Relatórios"),
    PermissionCode.PROFIT_VIEW: ("Visualizar lucro", "Financeiro"),
    PermissionCode.USERS_MANAGE: ("Gerenciar funcionários", "Equipe"),
    PermissionCode.AUDIT_VIEW: ("Visualizar auditoria", "Equipe"),
    PermissionCode.SETTINGS_VIEW: ("Visualizar configurações", "Geral"),
}


DEFAULT_PROFILE_PERMISSIONS = {
    "ADMIN": list(PermissionCode),
    "GERENTE": [
        PermissionCode.DASHBOARD_VIEW,
        PermissionCode.CASHIER_OPERATE,
        PermissionCode.CASH_REGISTER_VIEW,
        PermissionCode.CASH_REGISTER_OPERATE,
        PermissionCode.CASH_REGISTER_MANAGE,
        PermissionCode.DISCOUNT_NORMAL,
        PermissionCode.DISCOUNT_SPECIAL,
        PermissionCode.PRODUCTS_VIEW,
        PermissionCode.PRODUCTS_MANAGE,
        PermissionCode.INVENTORY_VIEW,
        PermissionCode.INVENTORY_MANAGE,
        PermissionCode.SALES_VIEW,
        PermissionCode.SALES_CANCEL,
        PermissionCode.SUPPLIERS_VIEW,
        PermissionCode.SUPPLIERS_MANAGE,
        PermissionCode.PURCHASES_VIEW,
        PermissionCode.PURCHASES_MANAGE,
        PermissionCode.LOTS_VIEW,
        PermissionCode.LOTS_MANAGE,
        PermissionCode.INVENTORY_COUNT,
        PermissionCode.CUSTOMERS_VIEW,
        PermissionCode.CUSTOMERS_MANAGE,
        PermissionCode.CREDIT_SELL,
        PermissionCode.CREDIT_RECEIVE,
        PermissionCode.CREDIT_MANAGE,
        PermissionCode.REPORTS_VIEW,
        PermissionCode.PROFIT_VIEW,
        PermissionCode.AUDIT_VIEW,
        PermissionCode.SETTINGS_VIEW,
    ],
    "CAIXA": [
        PermissionCode.CASHIER_OPERATE,
        PermissionCode.CASH_REGISTER_VIEW,
        PermissionCode.CASH_REGISTER_OPERATE,
        PermissionCode.DISCOUNT_NORMAL,
        PermissionCode.CUSTOMERS_VIEW,
        PermissionCode.CREDIT_SELL,
        PermissionCode.CREDIT_RECEIVE,
    ],
    "ESTOQUE": [
        PermissionCode.DASHBOARD_VIEW,
        PermissionCode.PRODUCTS_VIEW,
        PermissionCode.PRODUCTS_MANAGE,
        PermissionCode.INVENTORY_VIEW,
        PermissionCode.INVENTORY_MANAGE,
        PermissionCode.SUPPLIERS_VIEW,
        PermissionCode.SUPPLIERS_MANAGE,
        PermissionCode.PURCHASES_VIEW,
        PermissionCode.PURCHASES_MANAGE,
        PermissionCode.LOTS_VIEW,
        PermissionCode.LOTS_MANAGE,
        PermissionCode.INVENTORY_COUNT,
    ],
}
