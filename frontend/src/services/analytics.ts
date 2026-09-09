import { api } from "./api";
import type { AnalyticsOverview } from "../types";

export const analyticsService = {
  overview: async (start: string, end: string, stoppedDays = 30) => (await api.get<AnalyticsOverview>("/analytics/overview", { params: { start, end, stopped_days: stoppedDays } })).data,
  exportCsv: async (report: string, start: string, end: string, stoppedDays = 30) => (await api.get<{ filename: string; content: string }>("/analytics/export", { params: { report, start, end, stopped_days: stoppedDays } })).data,
};

export function downloadCsv(filename: string, content: string) {
  const url = URL.createObjectURL(new Blob([content], { type: "text/csv;charset=utf-8" }));
  const anchor = document.createElement("a");
  anchor.href = url; anchor.download = filename; anchor.click(); URL.revokeObjectURL(url);
}
