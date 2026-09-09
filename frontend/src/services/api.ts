export const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

type Primitive = string | number | boolean;
type QueryValue = Primitive | null | undefined;

interface RequestOptions {
  params?: Record<string, QueryValue>;
}

interface ApiResponse<T> {
  data: T;
}

export class ApiError extends Error {
  response: { data: unknown; status: number };

  constructor(message: string, status: number, data: unknown) {
    super(message);
    this.name = "ApiError";
    this.response = { data, status };
  }
}

function buildUrl(path: string, params?: Record<string, QueryValue>) {
  const url = new URL(path, API_URL);

  if (params) {
    Object.entries(params).forEach(([key, value]) => {
      if (value !== undefined && value !== null) {
        url.searchParams.set(key, String(value));
      }
    });
  }

  return url.toString();
}

async function parseBody(response: Response) {
  const contentType = response.headers.get("content-type") ?? "";

  if (contentType.includes("application/json")) {
    return response.json();
  }

  const text = await response.text();
  return text ? { detail: text } : null;
}

function getErrorDetail(data: unknown) {
  if (typeof data !== "object" || data === null || !("detail" in data)) {
    return null;
  }

  const detail = (data as { detail?: unknown }).detail;
  if (typeof detail === "string") {
    return detail;
  }
  if (typeof detail === "object" && detail !== null && "message" in detail && typeof detail.message === "string") {
    return detail.message;
  }

  if (Array.isArray(detail)) {
    const messages = detail
      .map((item) => {
        if (typeof item !== "object" || item === null || !("msg" in item)) return null;
        return typeof item.msg === "string" ? item.msg : null;
      })
      .filter((message): message is string => Boolean(message));
    return messages.length ? messages.join(" ") : null;
  }

  return null;
}

async function request<T>(method: string, path: string, body?: unknown, options?: RequestOptions): Promise<ApiResponse<T>> {
  const token = localStorage.getItem("vendifacil:token");
  let response: Response;
  let timeout: number | undefined;
  try {
    const controller = new AbortController();
    timeout = window.setTimeout(() => controller.abort(), 10000);
    response = await fetch(buildUrl(path, options?.params), {
      method,
      headers: {
        "Content-Type": "application/json",
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
      },
      body: body === undefined ? undefined : JSON.stringify(body),
      signal: controller.signal,
    });
  } catch {
    throw new ApiError("Não foi possível conectar ao servidor. Verifique se o backend está ligado na porta 8000.", 0, null);
  } finally {
    if (timeout !== undefined) window.clearTimeout(timeout);
  }

  const data = await parseBody(response);

  if (!response.ok) {
    const detail = getErrorDetail(data) ?? "Erro na comunicação com a API.";

    throw new ApiError(detail, response.status, data);
  }

  return { data: data as T };
}

export const api = {
  get: <T>(path: string, options?: RequestOptions) => request<T>("GET", path, undefined, options),
  post: <T>(path: string, body?: unknown, options?: RequestOptions) => request<T>("POST", path, body, options),
  put: <T>(path: string, body?: unknown, options?: RequestOptions) => request<T>("PUT", path, body, options),
  delete: <T>(path: string, options?: RequestOptions) => request<T>("DELETE", path, undefined, options),
};
