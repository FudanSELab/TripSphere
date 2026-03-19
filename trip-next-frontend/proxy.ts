import { NextRequest, NextResponse } from "next/server";
import { verifyToken } from "@/lib/session";

const GUEST_ONLY_ROUTES = ["/signin", "/signup"];
const AUTHENTICATED_ROUTES = ["/orders", "/profile", "/itinerary"];

export default async function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const token = request.cookies.get("session")?.value;
  const session = token ? await verifyToken(token) : null;

  // Strip client-sent headers to prevent spoofing
  const requestHeaders = new Headers(request.headers);
  requestHeaders.delete("x-user-id");
  requestHeaders.delete("x-user-roles");
  requestHeaders.delete("authorization");

  if (session) {
    // Inject verified user info into request headers
    requestHeaders.set("x-user-id", session.userId);
    requestHeaders.set("x-user-roles", session.roles.join(","));
    requestHeaders.set("authorization", `Bearer ${token}`);

    // Authenticated users should not access guest-only routes
    if (GUEST_ONLY_ROUTES.some((route) => pathname.startsWith(route))) {
      return NextResponse.redirect(new URL("/", request.url));
    }
  } else {
    if (AUTHENTICATED_ROUTES.some((route) => pathname.startsWith(route))) {
      return NextResponse.redirect(new URL("/signin", request.url));
    }
  }

  return NextResponse.next({
    request: { headers: requestHeaders },
  });
}

export const config = {
  matcher: [
    "/((?!_next/static|_next/image|favicon.ico|sitemap.xml|robots.txt).*)",
  ],
};
