import { api } from "./api";
import type { CashRegister } from "../types";

export const cashRegisterService = {
  current: async () => (await api.get<CashRegister | null>("/cash-registers/current")).data,
  history: async () => (await api.get<CashRegister[]>("/cash-registers")).data,
  get: async (id: number) => (await api.get<CashRegister>(`/cash-registers/${id}`)).data,
  open: async (opening_balance: number) => (await api.post<CashRegister>("/cash-registers/open", { opening_balance })).data,
  withdrawal: async (amount: number, reason: string) => (await api.post<CashRegister>("/cash-registers/withdrawal", { amount, reason })).data,
  supply: async (amount: number, reason: string) => (await api.post<CashRegister>("/cash-registers/supply", { amount, reason })).data,
  close: async (counted_balance: number, note?: string) => (await api.post<CashRegister>("/cash-registers/close", { counted_balance, note })).data,
};
