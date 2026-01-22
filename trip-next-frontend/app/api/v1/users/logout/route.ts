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
  response.cookies.set("token", "", {
    httpOnly: true,
    secure: process.env.NODE_ENV === "production",
    sameSite: "lax",
    maxAge: 0, // immediately expire
    path: "/",
  });

  return response;
}
