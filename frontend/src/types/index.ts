export type UserRole = "ADMIN" | "GERENTE" | "CAIXA" | "ESTOQUE";

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
  profile_name: string;
  permissions: string[];
  active: boolean;
  created_at: string;
  account: Account;
}

export interface StaffUser {
  id: number;
  name: string;
  email: string;
  role: UserRole;
  profile_name: string;
  active: boolean;
  created_at: string;
}

export interface Permission {
  code: string;
  name: string;
  module: string;
}

export interface Profile {
  id: number;
  name: string;
  code: UserRole;
  active: boolean;
  is_system: boolean;
  permissions: Permission[];
}

export interface AuditLog {
  id: number;
  user_name?: string | null;
  action: string;
  entity_type: string;
  entity_id?: string | null;
  description: string;
  changes?: Record<string, unknown> | null;
  created_at: string;
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
  trade_name?: string | null;
  cnpj?: string | null;
  phone?: string | null;
  whatsapp?: string | null;
  email?: string | null;
  address?: string | null;
  city?: string | null;
  state?: string | null;
  notes?: string | null;
  active: boolean;
  created_at: string;
  updated_at: string;
  products_count: number;
}

export interface Product {
  id: number;
  name: string;
  brand?: string | null;
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
  product_unit: string;
  quantity: number;
  unit_price: number;
  discount: number;
  subtotal: number;
}

export interface Sale {
  id: number;
  number: string;
  user_id: number;
  operator_name: string;
  cash_register_id?: number | null;
  customer_id?: number | null;
  customer_name?: string | null;
  credit_due_date?: string | null;
  subtotal: number;
  discount: number;
  surcharge: number;
  total: number;
  payment_method: string;
  amount_received?: number | null;
  change_amount?: number | null;
  status: string;
  note?: string | null;
  cancellation_reason?: string | null;
  cancelled_at?: string | null;
  created_at: string;
  items: SaleItem[];
  payments: SalePayment[];
}

export interface SalePayment {
  id: number;
  method: string;
  amount: number;
  amount_received?: number | null;
  change_amount: number;
}

export interface CashSummary {
  opening_balance: number;
  cash_sales: number;
  pix_sales: number;
  debit_sales: number;
  credit_sales: number;
  total_sales: number;
  supplies: number;
  withdrawals: number;
  refunds: number;
  credit_receipts: number;
  expected_cash: number;
}

export interface ProductSupplier {
  id: number;
  product_id: number;
  product_name: string;
  supplier_id: number;
  supplier_name: string;
  supplier_code?: string | null;
  last_price?: number | null;
  last_purchase_at?: string | null;
  preferred: boolean;
  lead_time_days?: number | null;
}

export interface PurchaseItem {
  id: number;
  product_id: number;
  product_name: string;
  product_unit: string;
  ordered_quantity: number;
  received_quantity: number;
  pending_quantity: number;
  unit_cost: number;
  subtotal: number;
  notes?: string | null;
}

export interface PurchaseOrder {
  id: number;
  number: string;
  supplier_id: number;
  supplier_name: string;
  created_by_name: string;
  order_date: string;
  expected_date?: string | null;
  notes?: string | null;
  subtotal: number;
  discount: number;
  total: number;
  status: string;
  created_at: string;
  updated_at: string;
  items: PurchaseItem[];
}

export interface PriceHistory {
  id: number;
  supplier_id: number;
  supplier_name: string;
  product_id: number;
  product_name: string;
  unit_cost: number;
  previous_cost?: number | null;
  variation_percent?: number | null;
  recorded_at: string;
}

export interface ProductLot {
  id: number;
  product_id: number;
  product_name: string;
  supplier_name?: string | null;
  lot_code?: string | null;
  initial_quantity: number;
  current_quantity: number;
  unit_cost: number;
  entry_date: string;
  expiration_date?: string | null;
  expiry_state: string;
  days_remaining?: number | null;
  status: string;
  created_at: string;
}

export interface InventoryLoss {
  id: number;
  product_name: string;
  lot_code?: string | null;
  quantity: number;
  reason: string;
  notes?: string | null;
  user_name: string;
  created_at: string;
}

export interface InventoryCountItem {
  id: number;
  product_id: number;
  product_name: string;
  system_quantity: number;
  counted_quantity?: number | null;
  difference?: number | null;
}

export interface InventoryCount {
  id: number;
  number: string;
  responsible_name: string;
  category_name?: string | null;
  notes?: string | null;
  status: string;
  created_at: string;
  completed_at?: string | null;
  positive_differences: number;
  negative_differences: number;
  items: InventoryCountItem[];
}

export interface CustomerDebt {
  id: number;
  sale_id: number;
  sale_number: string;
  amount: number;
  balance: number;
  due_date?: string | null;
  status: string;
  is_overdue: boolean;
  days_open: number;
  created_at: string;
}

export interface CustomerPayment {
  id: number;
  amount: number;
  method: string;
  responsible_name: string;
  balance_before: number;
  balance_after: number;
  notes?: string | null;
  created_at: string;
}

export interface Customer {
  id: number;
  name: string;
  phone?: string | null;
  whatsapp?: string | null;
  cpf?: string | null;
  address?: string | null;
  notes?: string | null;
  credit_limit?: number | null;
  credit_blocked: boolean;
  active: boolean;
  balance: number;
  available_credit?: number | null;
  total_purchased: number;
  ticket_average: number;
  last_purchase_at?: string | null;
  overdue_balance: number;
  created_at: string;
  updated_at: string;
  debts: CustomerDebt[];
  payments: CustomerPayment[];
  sales: Array<{ id: number; number: string; total: number; payment_method: string; status: string; created_at: string }>;
}

export interface CashRegister {
  id: number;
  operator_name: string;
  closed_by_name?: string | null;
  opened_at: string;
  closed_at?: string | null;
  opening_balance: number;
  expected_balance?: number | null;
  counted_balance?: number | null;
  difference?: number | null;
  status: string;
  closing_note?: string | null;
  summary: CashSummary;
  movements: Array<{ id: number; type: string; amount: number; reason?: string | null; created_at: string }>;
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
