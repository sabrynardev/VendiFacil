import { api } from "./api";
import type { Category, Product, Supplier } from "../types";

export const catalogService = {
  listProducts: async (filters?: { search?: string; category_id?: number; status?: string; low_stock?: boolean }) =>
    (await api.get<Product[]>("/products", { params: filters })).data,
  getProductByBarcode: async (barcode: string) => (await api.get<Product>(`/products/barcode/${barcode}`)).data,
  createProduct: async (payload: Partial<Product>) => (await api.post<Product>("/products", payload)).data,
  updateProduct: async (id: number, payload: Partial<Product>) => (await api.put<Product>(`/products/${id}`, payload)).data,
  deleteProduct: async (id: number) => api.delete(`/products/${id}`),
  listCategories: async () => (await api.get<Category[]>("/categories")).data,
  createCategory: async (payload: Partial<Category>) => (await api.post<Category>("/categories", payload)).data,
  updateCategory: async (id: number, payload: Partial<Category>) => (await api.put<Category>(`/categories/${id}`, payload)).data,
  deleteCategory: async (id: number) => api.delete(`/categories/${id}`),
  listSuppliers: async () => (await api.get<Supplier[]>("/suppliers")).data,
  createSupplier: async (payload: Partial<Supplier>) => (await api.post<Supplier>("/suppliers", payload)).data,
  updateSupplier: async (id: number, payload: Partial<Supplier>) => (await api.put<Supplier>(`/suppliers/${id}`, payload)).data,
  deleteSupplier: async (id: number) => api.delete(`/suppliers/${id}`),
};
