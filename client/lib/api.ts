// The browser calls FastAPI directly: a ZIP ingest runs for minutes, longer than a
// Vercel function lives, so it cannot go through a same-origin proxy.
export const API = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8001";

export async function api(path: string, init: RequestInit = {}) {
  const res = await fetch(`${API}${path}`, { credentials: "include", ...init });
  if (res.status === 401 && window.location.pathname !== "/login") {
    window.location.href = "/login";
  }
  return res;
}
