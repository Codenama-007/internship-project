// The browser calls FastAPI directly: a ZIP ingest runs for minutes, longer than a
// Vercel function lives, so it cannot go through a same-origin proxy.
// URL lives in client/.env.local (NEXT_PUBLIC_API_URL); Vercel sets its own copy.
export const API = process.env.NEXT_PUBLIC_API_URL!;

export async function api(path: string, init: RequestInit = {}) {
  const res = await fetch(`${API}${path}`, { credentials: "include", ...init });
  if (res.status === 401 && window.location.pathname !== "/login") {
    window.location.href = "/login";
  }
  return res;
}
