import { api } from "./api";
import type { Sale } from "../types";

export interface SalePayload {
  items: Array<{ product_id: number; quantity: number; discount: number }>;
  discount: number;
  payment_method: string;
  amount_received?: number;
}

export const salesService = {
  list: async () => (await api.get<Sale[]>("/sales")).data,
  create: async (payload: SalePayload) => (await api.post<Sale>("/sales", payload)).data,
};
