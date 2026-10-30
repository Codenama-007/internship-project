import { NextResponse } from "next/server";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8001";

// Same-origin proxy: the dev rewrite drops long requests (socket hang up), and an
// ingest takes minutes.
export async function POST(request: Request) {
  const form = await request.formData();
  const res = await fetch(`${API_URL}/api/ingest/zip`, {
    method: "POST",
    headers: { cookie: request.headers.get("cookie") ?? "" },
    body: form,
  });

  return new NextResponse(await res.text(), {
    status: res.status,
    headers: { "content-type": res.headers.get("content-type") ?? "application/json" },
  });
}
