import { api } from "./api";
import type {
  CategorySalesPoint,
  DashboardSummary,
  PaymentMethodPoint,
  RevenuePoint,
  StockAlert,
  TopProductPoint,
} from "../types";

export const dashboardService = {
  getSummary: async () => (await api.get<DashboardSummary>("/dashboard/summary")).data,
  getRevenue: async () => (await api.get<RevenuePoint[]>("/dashboard/revenue")).data,
  getTopProducts: async () => (await api.get<TopProductPoint[]>("/dashboard/top-products")).data,
  getPaymentMethods: async () => (await api.get<PaymentMethodPoint[]>("/dashboard/payment-methods")).data,
  getCategorySales: async () => (await api.get<CategorySalesPoint[]>("/dashboard/category-sales")).data,
  getAlerts: async () => (await api.get<StockAlert[]>("/inventory/alerts")).data,
};
