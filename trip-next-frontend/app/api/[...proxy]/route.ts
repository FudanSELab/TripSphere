import { NextRequest } from "next/server";
import { proxyHandler } from "./handler";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

export async function GET(req: NextRequest) {
  return proxyHandler(req);
}

export async function POST(req: NextRequest) {
  return proxyHandler(req);
}

export async function PUT(req: NextRequest) {
  return proxyHandler(req);
}

export async function PATCH(req: NextRequest) {
  return proxyHandler(req);
}

export async function DELETE(req: NextRequest) {
  return proxyHandler(req);
}
