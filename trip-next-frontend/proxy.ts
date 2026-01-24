import { NextRequest, NextResponse } from "next/server";

// Routes that should redirect to home if user is already authenticated
const guestOnlyRoutes = ["/login", "/signup"];

// Routes that require authentication (redirect to login if not authenticated)
// Add routes here as needed, e.g., ["/profile", "/settings", "/my-trips"]
const protectedRoutes: string[] = [];

export function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl;
  const token = request.cookies.get("token")?.value;

  // If user has a token and tries to access guest-only routes, redirect to home
  if (token && guestOnlyRoutes.some((route) => pathname.startsWith(route))) {
    return NextResponse.redirect(new URL("/", request.url));
  }

  // If user doesn't have a token and tries to access protected routes, redirect to login
  if (!token && protectedRoutes.some((route) => pathname.startsWith(route))) {
    const loginUrl = new URL("/login", request.url);
    loginUrl.searchParams.set("redirect", pathname);
    return NextResponse.redirect(loginUrl);
  }

  return NextResponse.next();
}

export const config = {
  matcher: [
    /*
     * Match all request paths except:
     * - api routes
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico, sitemap.xml, robots.txt (metadata files)
     * - public folder files
     */
    "/((?!api|_next/static|_next/image|favicon.ico|sitemap.xml|robots.txt|.*\\.png$|.*\\.jpg$|.*\\.svg$).*)",
  ],
};
