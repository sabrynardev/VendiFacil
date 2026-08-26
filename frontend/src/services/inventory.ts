import { api } from "./api";
import type { InventoryRecord, StockMovement } from "../types";

export const inventoryService = {
  list: async () => (await api.get<InventoryRecord[]>("/inventory")).data,
  predictions: async () => (await api.get<InventoryRecord[]>("/inventory/predictions")).data,
  movements: async () => (await api.get<StockMovement[]>("/inventory/movements")).data,
};
