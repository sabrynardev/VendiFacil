export type UserRole = "ADMIN" | "CAIXA" | "ESTOQUE";

export interface Account {
  id: number;
  name: string;
  active: boolean;
  created_at: string;
}

export interface User {
  id: number;
  account_id: number;
  name: string;
  email: string;
  role: UserRole;
  active: boolean;
  created_at: string;
  account: Account;
}

export interface Category {
  id: number;
  name: string;
  description?: string | null;
  created_at: string;
}

export interface Supplier {
  id: number;
  name: string;
  cnpj?: string | null;
  phone?: string | null;
  whatsapp?: string | null;
  email?: string | null;
  address?: string | null;
  notes?: string | null;
  created_at: string;
  products_count: number;
}

export interface Product {
  id: number;
  name: string;
  description?: string | null;
  sku: string;
  barcode?: string | null;
  category_id?: number | null;
  supplier_id?: number | null;
  cost_price: number;
  sale_price: number;
  stock_quantity: number;
  minimum_stock: number;
  unit: string;
  active: boolean;
  created_at: string;
  updated_at: string;
  category_name?: string | null;
  supplier_name?: string | null;
  margin: number;
  margin_percent: number;
  stock_status: string;
}

export interface SaleItem {
  id: number;
  product_id: number;
  product_name: string;
  quantity: number;
  unit_price: number;
  discount: number;
  subtotal: number;
}

export interface Sale {
  id: number;
  user_id: number;
  operator_name: string;
  subtotal: number;
  discount: number;
  total: number;
  payment_method: string;
  amount_received?: number | null;
  change_amount?: number | null;
  status: string;
  created_at: string;
  items: SaleItem[];
}

export interface InventoryRecord {
  product_id: number;
  product_name: string;
  sku: string;
  category_name?: string | null;
  stock_quantity: number;
  minimum_stock: number;
  average_sales_per_day: number;
  days_remaining?: number | null;
  purchase_recommendation: number;
  status: string;
}

export interface StockAlert {
  product_id: number;
  product_name: string;
  stock_quantity: number;
  minimum_stock: number;
  status: string;
}

export interface StockMovement {
  id: number;
  product_name: string;
  quantity: number;
  previous_stock: number;
  new_stock: number;
  type: string;
  user_name?: string | null;
  reason?: string | null;
  created_at: string;
}

export interface DashboardSummary {
  revenue_today: { value: number; delta: number };
  sales_today: { value: number; delta: number };
  average_ticket: { value: number; delta: number };
  low_stock_products: number;
}

export interface RevenuePoint {
  day: string;
  revenue: number;
}

export interface CategorySalesPoint {
  category: string;
  sales: number;
}

export interface PaymentMethodPoint {
  method: string;
  total: number;
}

export interface TopProductPoint {
  product: string;
  quantity: number;
}

export interface ReportSummary {
  period: string;
  revenue: number;
  sales_count: number;
  average_ticket: number;
  estimated_profit: number;
  items_sold: number;
}
