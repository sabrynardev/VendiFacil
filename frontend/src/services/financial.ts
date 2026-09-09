import { api } from "./api";
import type { CashFlowEntry, FinancialCategory, FinancialProjection, FinancialReceivable, FinancialSummary, ManualRevenue, Payable, RecurringExpense } from "../types";

export const financialService = {
  categories: async () => (await api.get<FinancialCategory[]>("/financial/categories")).data,
  createCategory: async (payload: unknown) => (await api.post<FinancialCategory>("/financial/categories", payload)).data,
  payables: async () => (await api.get<Payable[]>("/financial/payables")).data,
  createPayable: async (payload: unknown) => (await api.post<Payable>("/financial/payables", payload)).data,
  pay: async (id: number, payload: unknown) => (await api.post(`/financial/payables/${id}/payments`, payload)).data,
  cancelPayable: async (id: number, reason: string) => (await api.post<Payable>(`/financial/payables/${id}/cancel`, undefined, { params: { reason } })).data,
  revenues: async () => (await api.get<ManualRevenue[]>("/financial/revenues")).data,
  createRevenue: async (payload: unknown) => (await api.post<ManualRevenue>("/financial/revenues", payload)).data,
  receivables: async () => (await api.get<FinancialReceivable[]>("/financial/receivables")).data,
  createReceivable: async (payload: unknown) => (await api.post<FinancialReceivable>("/financial/receivables", payload)).data,
  receive: async (id: number, payload: unknown) => (await api.post(`/financial/receivables/${id}/receipts`, payload)).data,
  recurring: async () => (await api.get<RecurringExpense[]>("/financial/recurring")).data,
  createRecurring: async (payload: unknown) => (await api.post<RecurringExpense>("/financial/recurring", payload)).data,
  generateRecurring: async () => (await api.post<Payable[]>("/financial/recurring/generate")).data,
  summary: async (start: string, end: string) => (await api.get<FinancialSummary>("/financial/summary", { params: { start, end } })).data,
  cashFlow: async (start: string, end: string) => (await api.get<CashFlowEntry[]>("/financial/cash-flow", { params: { start, end } })).data,
  projections: async () => (await api.get<FinancialProjection[]>("/financial/projections")).data,
};
