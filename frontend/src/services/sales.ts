import { api } from "./api";
import type { Sale } from "../types";

export interface SalePayload {
  items: Array<{ product_id: number; quantity: number; discount: number }>;
  discount: number;
  surcharge?: number;
  payments: Array<{ method: string; amount: number; amount_received?: number }>;
  note?: string;
  idempotency_key?: string;
  authorization_email?: string;
  authorization_password?: string;
}

export const salesService = {
  list: async (filters?: { status?: string; payment_method?: string; operator_id?: number; date_from?: string; date_to?: string }) => (await api.get<Sale[]>("/sales", { params: filters })).data,
  create: async (payload: SalePayload) => (await api.post<Sale>("/sales", payload)).data,
  hold: async (payload: Omit<SalePayload, "payments">) => (await api.post<Sale>("/sales/hold", payload)).data,
  completeHeld: async (id: number, payload: SalePayload) => (await api.post<Sale>(`/sales/${id}/complete`, payload)).data,
  cancel: async (id: number, reason: string) => (await api.post<Sale>(`/sales/${id}/cancel`, { reason })).data,
};
