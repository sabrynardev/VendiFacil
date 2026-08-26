import { api } from "./api";
import type { ReportSummary } from "../types";

export const reportsService = {
  summary: async (period: string) => (await api.get<ReportSummary>("/reports", { params: { period } })).data,
};
