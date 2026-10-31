// The browser calls FastAPI directly: a ZIP ingest runs for minutes, longer than a
// Vercel function lives, so it cannot go through a same-origin proxy.
// URL lives in client/.env.local (NEXT_PUBLIC_LIVE_URL); Vercel sets its own copy.
// The NEXT_PUBLIC_ prefix is required: only those vars reach the browser bundle.
export const API = process.env.NEXT_PUBLIC_LIVE_URL!;

// shortcut: token in localStorage, readable by JS. The httpOnly cookie is not sent
// cross-site (vercel.app -> onrender.com), so this is the reliable path. Upgrade: put
// both apps on one site (app./api.example.com) and drop this in favour of the cookie.
const TOKEN_KEY = "bd_token";

export function saveToken(token: string) {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken() {
  localStorage.removeItem(TOKEN_KEY);
}

export async function api(path: string, init: RequestInit = {}) {
  const headers = new Headers(init.headers);
  const token = localStorage.getItem(TOKEN_KEY);
  if (token) headers.set("Authorization", `Bearer ${token}`);
  const res = await fetch(`${API}${path}`, { credentials: "include", ...init, headers });
  if (res.status === 401) {
    clearToken();
    if (window.location.pathname !== "/login") window.location.href = "/login";
  }
  return res;
}
