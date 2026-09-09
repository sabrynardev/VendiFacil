import { api } from "./api";
import type { AskVendiResponse, IntelligenceOverview } from "../types";

export const intelligenceService = {
  insights: async (start: string, end: string, category?: string, priority?: string) => (
    await api.get<IntelligenceOverview>("/intelligence/insights", { params: { start, end, category: category || undefined, priority: priority || undefined } })
  ).data,
  ask: async (question: string, start?: string, end?: string) => (
    await api.post<AskVendiResponse>("/intelligence/ask", { question, start, end })
  ).data,
};
