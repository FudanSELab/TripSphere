import { ResponseCode } from "@/lib/requests/base/code";
import { ResponseWrap } from "@/lib/requests/base/request";
import { NextRequest, NextResponse } from "next/server";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function POST(_: NextRequest) {
  const response = NextResponse.json<ResponseWrap<Record<string, never>>>({
    data: {},
    code: ResponseCode.SUCCESS,
    msg: "Logout successful",
  });

  // remove token from cookie
  // Only use secure cookies when HTTPS is enabled
  // Set COOKIE_SECURE=true in production with HTTPS
  const isSecure = process.env.COOKIE_SECURE === "true";
  response.cookies.set("token", "", {
    httpOnly: true,
    secure: isSecure,
    sameSite: "lax",
    maxAge: 0, // immediately expire
    path: "/",
  });

  return response;
}
