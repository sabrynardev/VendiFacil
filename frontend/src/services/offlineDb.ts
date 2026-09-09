import type { CashRegister, Product } from "../types";
import type { SalePayload } from "./sales";

const DB_NAME = "vendi-offline";
const DB_VERSION = 1;

export interface CachedProduct extends Product {
  account_id: number;
  confirmed_stock: number;
  pending_quantity: number;
}

export interface OfflineSalePayload extends SalePayload {
  operation_id: string;
  device_id: string;
  local_created_at: string;
  cash_register_id?: number;
  items: Array<{ product_id: number; quantity: number; discount: number; unit_price: number; product_updated_at?: string }>;
}

export interface QueueOperation {
  operation_id: string;
  account_id: number;
  user_id: number;
  type: "SALE";
  payload: OfflineSalePayload;
  created_at: string;
  attempts: number;
  status: "PENDING" | "SYNCING" | "ATTENTION";
  error?: string;
  next_attempt_at?: string;
}

export interface OfflineDraft {
  key: string;
  account_id: number;
  user_id: number;
  cart: Array<{ product: Product; quantity: number; discount: number }>;
  discount: number;
  surcharge: number;
  note: string;
  customer_id?: number;
  kind?: "CURRENT" | "HELD";
  updated_at: string;
}

export interface OfflineSession {
  key: string;
  account_id: number;
  user_id: number;
  cached_at: string;
  register: CashRegister | null;
}

function openDatabase(): Promise<IDBDatabase> {
  return new Promise((resolve, reject) => {
    const request = indexedDB.open(DB_NAME, DB_VERSION);
    request.onupgradeneeded = () => {
      const db = request.result;
      if (!db.objectStoreNames.contains("products")) db.createObjectStore("products", { keyPath: ["account_id", "id"] });
      if (!db.objectStoreNames.contains("queue")) db.createObjectStore("queue", { keyPath: "operation_id" });
      if (!db.objectStoreNames.contains("drafts")) db.createObjectStore("drafts", { keyPath: "key" });
      if (!db.objectStoreNames.contains("meta")) db.createObjectStore("meta", { keyPath: "key" });
    };
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
  });
}

async function run<T>(storeName: string, mode: IDBTransactionMode, action: (store: IDBObjectStore) => IDBRequest<T>): Promise<T> {
  const db = await openDatabase();
  return new Promise((resolve, reject) => {
    const transaction = db.transaction(storeName, mode);
    const request = action(transaction.objectStore(storeName));
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
    transaction.oncomplete = () => db.close();
    transaction.onerror = () => reject(transaction.error);
  });
}

export async function cacheProducts(accountId: number, products: Product[]) {
  const existing = new Map((await cachedProducts(accountId)).map(product => [product.id, product]));
  const db = await openDatabase();
  await new Promise<void>((resolve, reject) => {
    const transaction = db.transaction("products", "readwrite");
    const store = transaction.objectStore("products");
    products.forEach(product => {
      const pending = existing.get(product.id)?.pending_quantity ?? 0;
      store.put({ ...product, account_id: accountId, confirmed_stock: product.stock_quantity, pending_quantity: pending, stock_quantity: product.stock_quantity - pending } satisfies CachedProduct);
    });
    transaction.oncomplete = () => resolve(); transaction.onerror = () => reject(transaction.error);
  });
  db.close();
}

export async function cachedProducts(accountId: number): Promise<CachedProduct[]> {
  const all = await run<CachedProduct[]>("products", "readonly", store => store.getAll());
  return all.filter(product => product.account_id === accountId && product.active);
}

export async function findCachedProduct(accountId: number, query: string): Promise<CachedProduct | undefined> {
  const normalized = query.trim().toLocaleLowerCase("pt-BR");
  const products = await cachedProducts(accountId);
  return products.find(product => product.barcode?.toLocaleLowerCase("pt-BR") === normalized || product.sku.toLocaleLowerCase("pt-BR") === normalized)
    ?? products.find(product => product.name.toLocaleLowerCase("pt-BR").includes(normalized));
}

export async function applyPendingStock(accountId: number, items: OfflineSalePayload["items"], direction: 1 | -1) {
  const db = await openDatabase();
  await new Promise<void>((resolve, reject) => {
    const transaction = db.transaction("products", "readwrite");
    const store = transaction.objectStore("products");
    items.forEach(item => {
      const request = store.get([accountId, item.product_id]);
      request.onsuccess = () => {
        const product = request.result as CachedProduct | undefined;
        if (product) store.put({ ...product, pending_quantity: product.pending_quantity + item.quantity * direction, stock_quantity: product.stock_quantity - item.quantity * direction });
      };
    });
    transaction.oncomplete = () => resolve(); transaction.onerror = () => reject(transaction.error);
  });
  db.close();
}

export async function confirmPendingStock(accountId: number, items: OfflineSalePayload["items"]) {
  const db = await openDatabase();
  await new Promise<void>((resolve, reject) => {
    const transaction = db.transaction("products", "readwrite");
    const store = transaction.objectStore("products");
    items.forEach(item => {
      const request = store.get([accountId, item.product_id]);
      request.onsuccess = () => {
        const product = request.result as CachedProduct | undefined;
        if (product) store.put({ ...product, pending_quantity: Math.max(product.pending_quantity - item.quantity, 0), confirmed_stock: product.stock_quantity });
      };
    });
    transaction.oncomplete = () => resolve(); transaction.onerror = () => reject(transaction.error);
  });
  db.close();
}

export const queueOperation = (operation: QueueOperation) => run("queue", "readwrite", store => store.put(operation));
export const removeOperation = (operationId: string) => run("queue", "readwrite", store => store.delete(operationId));
export const allOperations = async () => (await run<QueueOperation[]>("queue", "readonly", store => store.getAll())).sort((a, b) => a.created_at.localeCompare(b.created_at));
export const saveDraft = (draft: OfflineDraft) => run("drafts", "readwrite", store => store.put(draft));
export const getDraft = (key: string) => run<OfflineDraft | undefined>("drafts", "readonly", store => store.get(key));
export const allDrafts = async () => (await run<OfflineDraft[]>("drafts", "readonly", store => store.getAll())).sort((a, b) => b.updated_at.localeCompare(a.updated_at));
export const removeDraft = (key: string) => run("drafts", "readwrite", store => store.delete(key));
export const saveSession = (session: OfflineSession) => run("meta", "readwrite", store => store.put(session));
export const getSession = (key: string) => run<OfflineSession | undefined>("meta", "readonly", store => store.get(key));

export function getDeviceId() {
  const key = "vendi:device-id";
  const existing = localStorage.getItem(key);
  if (existing) return existing;
  const created = `CAIXA-${crypto.randomUUID()}`;
  localStorage.setItem(key, created);
  return created;
}
