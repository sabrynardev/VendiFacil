from enum import StrEnum


class PermissionCode(StrEnum):
    DASHBOARD_VIEW = "dashboard.view"
    CASHIER_OPERATE = "cashier.operate"
    PRODUCTS_VIEW = "products.view"
    PRODUCTS_MANAGE = "products.manage"
    INVENTORY_VIEW = "inventory.view"
    INVENTORY_MANAGE = "inventory.manage"
    SALES_VIEW = "sales.view"
    SALES_CANCEL = "sales.cancel"
    SUPPLIERS_VIEW = "suppliers.view"
    SUPPLIERS_MANAGE = "suppliers.manage"
    REPORTS_VIEW = "reports.view"
    PROFIT_VIEW = "profit.view"
    USERS_MANAGE = "users.manage"
    AUDIT_VIEW = "audit.view"
    SETTINGS_VIEW = "settings.view"


PERMISSION_LABELS = {
    PermissionCode.DASHBOARD_VIEW: ("Visualizar dashboard", "Geral"),
    PermissionCode.CASHIER_OPERATE: ("Operar PDV", "Caixa"),
    PermissionCode.PRODUCTS_VIEW: ("Visualizar produtos", "Produtos"),
    PermissionCode.PRODUCTS_MANAGE: ("Gerenciar produtos", "Produtos"),
    PermissionCode.INVENTORY_VIEW: ("Visualizar estoque", "Estoque"),
    PermissionCode.INVENTORY_MANAGE: ("Movimentar estoque", "Estoque"),
    PermissionCode.SALES_VIEW: ("Visualizar vendas", "Vendas"),
    PermissionCode.SALES_CANCEL: ("Cancelar vendas", "Vendas"),
    PermissionCode.SUPPLIERS_VIEW: ("Visualizar fornecedores", "Fornecedores"),
    PermissionCode.SUPPLIERS_MANAGE: ("Gerenciar fornecedores", "Fornecedores"),
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
        PermissionCode.PRODUCTS_VIEW,
        PermissionCode.PRODUCTS_MANAGE,
        PermissionCode.INVENTORY_VIEW,
        PermissionCode.INVENTORY_MANAGE,
        PermissionCode.SALES_VIEW,
        PermissionCode.SALES_CANCEL,
        PermissionCode.SUPPLIERS_VIEW,
        PermissionCode.SUPPLIERS_MANAGE,
        PermissionCode.REPORTS_VIEW,
        PermissionCode.PROFIT_VIEW,
        PermissionCode.AUDIT_VIEW,
        PermissionCode.SETTINGS_VIEW,
    ],
    "CAIXA": [PermissionCode.CASHIER_OPERATE],
    "ESTOQUE": [
        PermissionCode.DASHBOARD_VIEW,
        PermissionCode.PRODUCTS_VIEW,
        PermissionCode.PRODUCTS_MANAGE,
        PermissionCode.INVENTORY_VIEW,
        PermissionCode.INVENTORY_MANAGE,
        PermissionCode.SUPPLIERS_VIEW,
        PermissionCode.SUPPLIERS_MANAGE,
    ],
}
