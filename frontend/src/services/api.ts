const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

type Primitive = string | number | boolean;
type QueryValue = Primitive | null | undefined;

interface RequestOptions {
  params?: Record<string, QueryValue>;
}

interface ApiResponse<T> {
  data: T;
}

class ApiError extends Error {
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

async function request<T>(method: string, path: string, body?: unknown, options?: RequestOptions): Promise<ApiResponse<T>> {
  const token = localStorage.getItem("vendifacil:token");
  const response = await fetch(buildUrl(path, options?.params), {
    method,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: body === undefined ? undefined : JSON.stringify(body),
  });

  const data = await parseBody(response);

  if (!response.ok) {
    const detail =
      typeof data === "object" && data !== null && "detail" in data && typeof (data as { detail?: unknown }).detail === "string"
        ? (data as { detail: string }).detail
        : "Erro na comunicação com a API.";

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
