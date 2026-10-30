import { NextResponse } from "next/server";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8001";

// The dev rewrite drops long requests (socket hang up past ~30s), so chat gets its own
// same-origin proxy. Everything else keeps using the /api/* rewrite.
export async function POST(request: Request) {
  const res = await fetch(`${API_URL}/api/chat`, {
    method: "POST",
    headers: {
      "content-type": "application/json",
      cookie: request.headers.get("cookie") ?? "",
    },
    body: await request.text(),
  });

  return new NextResponse(res.body, {
    status: res.status,
    headers: { "content-type": res.headers.get("content-type") ?? "application/json" },
  });
}
