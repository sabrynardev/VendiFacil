import { api } from "./api";
import type { Customer, CustomerPayment, InventoryCount, InventoryLoss, PriceHistory, ProductLot, ProductSupplier, PurchaseOrder } from "../types";

export const purchaseService = {
  list: async (filters?: { status?: string; supplier_id?: number }) => (await api.get<PurchaseOrder[]>("/purchases", { params: filters })).data,
  create: async (payload: Record<string, unknown>) => (await api.post<PurchaseOrder>("/purchases", payload)).data,
  receive: async (id: number, payload: Record<string, unknown>) => (await api.post<PurchaseOrder>(`/purchases/${id}/receive`, payload)).data,
  cancel: async (id: number) => (await api.post<PurchaseOrder>(`/purchases/${id}/cancel`)).data,
  priceHistory: async () => (await api.get<PriceHistory[]>("/purchases/history/prices")).data,
  supplierProducts: async (supplierId: number) => (await api.get<ProductSupplier[]>(`/purchases/suppliers/${supplierId}/products`)).data,
  linkProduct: async (supplierId: number, payload: Record<string, unknown>) => (await api.post<ProductSupplier>(`/purchases/suppliers/${supplierId}/products`, payload)).data,
};

export const managementInventoryService = {
  lots: async () => (await api.get<ProductLot[]>("/management-inventory/lots")).data,
  expiryAlerts: async () => (await api.get<ProductLot[]>("/management-inventory/expiry-alerts")).data,
  createLot: async (payload: Record<string, unknown>) => (await api.post<ProductLot>("/management-inventory/lots", payload)).data,
  losses: async () => (await api.get<InventoryLoss[]>("/management-inventory/losses")).data,
  createLoss: async (payload: Record<string, unknown>) => (await api.post<InventoryLoss>("/management-inventory/losses", payload)).data,
  counts: async () => (await api.get<InventoryCount[]>("/management-inventory/counts")).data,
  createCount: async (payload: Record<string, unknown>) => (await api.post<InventoryCount>("/management-inventory/counts", payload)).data,
  completeCount: async (id: number, items: Array<{ product_id: number; counted_quantity: number }>) => (await api.post<InventoryCount>(`/management-inventory/counts/${id}/complete`, { items })).data,
  cancelCount: async (id: number) => (await api.post<InventoryCount>(`/management-inventory/counts/${id}/cancel`)).data,
};

export const customerService = {
  list: async (search?: string) => (await api.get<Customer[]>("/customers", { params: { search: search || undefined } })).data,
  get: async (id: number) => (await api.get<Customer>(`/customers/${id}`)).data,
  create: async (payload: Record<string, unknown>) => (await api.post<Customer>("/customers", payload)).data,
  update: async (id: number, payload: Record<string, unknown>) => (await api.put<Customer>(`/customers/${id}`, payload)).data,
  pay: async (id: number, payload: Record<string, unknown>) => (await api.post<CustomerPayment>(`/customers/${id}/payments`, payload)).data,
};
