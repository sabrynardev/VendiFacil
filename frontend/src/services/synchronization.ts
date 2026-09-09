import { api, ApiError, API_URL } from "./api";
import { allOperations, confirmPendingStock, queueOperation, removeOperation, type QueueOperation } from "./offlineDb";

export interface ServerSyncLog {
  operation_id: string;
  operation_type: string;
  device_id: string;
  status: string;
  attempts: number;
  conflict: boolean;
  error_category?: string | null;
  error_message?: string | null;
  duration_ms: number;
  created_at: string;
  updated_at: string;
}

export async function backendAvailable() {
  const controller = new AbortController();
  const timeout = window.setTimeout(() => controller.abort(), 3000);
  try {
    const response = await fetch(`${API_URL}/health`, { signal: controller.signal, cache: "no-store" });
    return response.ok && (await response.json()).database === "ok";
  } catch { return false; }
  finally { window.clearTimeout(timeout); }
}

export async function synchronizeQueue(accountId: number, userId: number) {
  const operations = (await allOperations()).filter(item => item.account_id === accountId && item.user_id === userId && item.status !== "ATTENTION");
  let synced = 0;
  for (const operation of operations) {
    if (operation.next_attempt_at && new Date(operation.next_attempt_at) > new Date()) continue;
    await queueOperation({ ...operation, status: "SYNCING" });
    try {
      await api.post("/sync/sales", operation.payload);
      await confirmPendingStock(accountId, operation.payload.items);
      await removeOperation(operation.operation_id);
      synced += 1;
    } catch (error) {
      const status = error instanceof ApiError ? error.response.status : 0;
      const attempts = operation.attempts + 1;
      const temporary = status === 0 || status >= 500;
      const delay = Math.min(2 ** attempts * 5, 300);
      await queueOperation({ ...operation, attempts, status: temporary ? "PENDING" : "ATTENTION", error: error instanceof Error ? error.message : "Falha de sincronização", next_attempt_at: temporary ? new Date(Date.now() + delay * 1000).toISOString() : undefined });
      if (temporary) break;
    }
  }
  return synced;
}

export const syncService = {
  logs: async () => (await api.get<ServerSyncLog[]>("/sync/logs")).data,
};
