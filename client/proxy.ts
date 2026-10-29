import { NextResponse, type NextRequest } from "next/server";

// Optimistic check only — FastAPI verifies the JWT on every real API call.
export function proxy(request: NextRequest) {
  const authed = request.cookies.has("bd_session");
  const { pathname } = request.nextUrl;

  if (pathname.startsWith("/app") && !authed) {
    return NextResponse.redirect(new URL("/login", request.url));
  }
  if (pathname === "/login" && authed) {
    return NextResponse.redirect(new URL("/app", request.url));
  }
  return NextResponse.next();
}

export const config = {
  matcher: ["/app/:path*", "/login"],
};
