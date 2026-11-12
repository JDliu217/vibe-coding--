export class ApiError extends Error {
  status: number;
  code: string;

  constructor(status: number, code: string, message: string) {
    super(message);
    this.status = status;
    this.code = code;
  }
}

export function yuan(cents: number) {
  return `¥${(cents / 100).toFixed(2)}`;
}

export function authHeader() {
  const token = localStorage.getItem("freshmart-token");
  return token ? { Authorization: `Bearer ${token}` } : {};
}

export async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  const headers = new Headers(options.headers);
  headers.set("Content-Type", "application/json");
  const token = typeof window === "undefined" ? "" : localStorage.getItem("freshmart-token");
  if (token) headers.set("Authorization", `Bearer ${token}`);
  const response = await fetch(path, { ...options, headers });
  const data = await response.json().catch(() => ({}));
  if (!response.ok) {
    const error = data.error || {};
    throw new ApiError(response.status, error.code || "REQUEST_FAILED", error.message || "请求失败");
  }
  return data as T;
}
