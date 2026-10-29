import { NextResponse } from "next/server";

// The dev rewrite drops long requests (socket hang up past ~30s), so chat gets its own
// same-origin proxy. Everything else keeps using the /api/* rewrite.
export async function POST(request: Request) {
  const res = await fetch("http://127.0.0.1:8000/api/chat", {
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
