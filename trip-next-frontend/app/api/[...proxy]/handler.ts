import * as grpc from "@grpc/grpc-js";
import { parse } from "cookie";
import { NextRequest, NextResponse } from "next/server";

import { mapGrpcCodeToHttp } from "@/app/api/[...proxy]/code";
import { grpcProxyMap, RpcProxyRule } from "@/app/api/[...proxy]/proxy-map";
import { grpcClient } from "@/lib/grpc/client";
import { Details } from "@/lib/grpc/gen/tripsphere/common/details";
import {
  GetCurrentUserRequest,
  GetCurrentUserResponse,
} from "@/lib/grpc/gen/tripsphere/user/user";
import { Reason, ResponseCode } from "@/lib/requests/base/code";
import { ResponseWrap } from "@/lib/requests/base/request";

const METHODS_WITH_BODY = new Set(["POST", "PUT", "PATCH", "DELETE"]);

export async function proxyHandler(req: NextRequest): Promise<NextResponse> {
  const pathname = req.nextUrl.pathname;

  if (!pathname.startsWith("/api")) {
    return NextResponse.json(
      { code: ResponseCode.NOT_FOUND, msg: "Not Found" },
      { status: 404 },
    );
  }

  const routeKey = `${req.method.toUpperCase()} ${pathname}`;
  const rule =
    grpcProxyMap[routeKey as keyof typeof grpcProxyMap] ??
    grpcProxyMap[pathname as keyof typeof grpcProxyMap];

  if (!rule) {
    return NextResponse.json(
      { code: ResponseCode.NOT_FOUND, msg: "Not Found" },
      { status: 404 },
    );
  }

  try {
    const body = METHODS_WITH_BODY.has(req.method.toUpperCase())
      ? await parseBody(req)
      : undefined;
    const grpcRequest = rule.buildRPCRequest(body as any);
    const metadata = await buildMetadata(req);
    const grpcResponse = await invokeRPC(rule, grpcRequest, metadata);
    const httpResponse = rule.buildHttpResponse(grpcResponse as any);

    const responseData: ResponseWrap<any> = {
      data: httpResponse,
      code: ResponseCode.SUCCESS,
      msg: "Success",
    };

    if (rule.httpResponseHook) {
      const nextResponse = rule.httpResponseHook({
        req,
        httpResponse: responseData,
      });
      if (nextResponse) {
        return nextResponse;
      }
    }

    return NextResponse.json(responseData);
  } catch (error) {
    const serviceError = error as grpc.ServiceError;
    const httpStatus =
      typeof serviceError.code === "number"
        ? mapGrpcCodeToHttp(serviceError.code)
        : 502;
    const responseCode = mapGrpcCodeToResponseCode(serviceError.code);
    const errorDetails = extractErrorDetails(serviceError);

    console.log("serviceError.message:", serviceError.message);
    const errorMessage = extractGrpcErrorMessage(serviceError);
    const responseData: ResponseWrap = {
      data: undefined,
      code: responseCode,
      msg: errorMessage,
      ...(errorDetails && { error: errorDetails }),
    };

    return NextResponse.json(responseData, { status: httpStatus });
  }
}

async function parseBody(req: NextRequest): Promise<unknown> {
  const clone = req.clone();
  const contentType = clone.headers.get("content-type") || "";

  if (contentType.includes("application/json")) {
    try {
      return await clone.json();
    } catch {
      return undefined;
    }
  }

  if (contentType.includes("application/x-www-form-urlencoded")) {
    const form = await clone.formData();
    return Object.fromEntries(form.entries());
  }

  const text = await clone.text();
  return text.length ? text : undefined;
}

// APIs that don't require calling getCurrentUser separately to get current user data
const WithoutAuthAPIs: string[] = [];
// const WithoutAuthAPIs = ['/api/user/login', '/api/user/register']

// Convert all request headers to gRPC metadata
// 1. Try to extract token from cookie and put it in gRPC metadata["authorization"]
// 2. Call user service grpc client user.getCurrentUser to get current user data
// 3. Set new metadata: metadata["uid"] = user id, metadata["roles"] = roles, metadata["authorization"] = token
// 4. Return metadata
async function buildMetadata(req: NextRequest): Promise<grpc.Metadata> {
  if (WithoutAuthAPIs.includes(req.nextUrl.pathname)) {
    return new grpc.Metadata();
  }

  const metadata = new grpc.Metadata();
  const token = parseCookieToken(req);

  console.log("token:", token);
  // If no token, return empty metadata directly
  if (!token) {
    return metadata;
  }

  try {
    // 1. Create temporary metadata for calling getCurrentUser
    console.log("authMetadata:");
    const authMetadata = new grpc.Metadata();
    authMetadata.add("authorization", `Bearer ${token}`);

    // 2. Call user service to get current user data
    const currentUserRequest = GetCurrentUserRequest.create({});
    console.log("currentUserRequest:", currentUserRequest);
    const userResponse = await new Promise<GetCurrentUserResponse>(
      (resolve, reject) => {
        grpcClient.user.getCurrentUser(
          currentUserRequest,
          authMetadata,
          (err, response) => {
            if (err) return reject(err);
            if (!response)
              return reject(new Error("Empty response from getCurrentUser"));
            resolve(response);
          },
        );
      },
    );

    // 3. Extract user information from response
    const user = userResponse.user;
    if (user) {
      const userId = user.id;
      const rolesList = user.roles;

      // 4. Set new metadata
      metadata.add("uid", userId.toString());
      metadata.add("roles", JSON.stringify(rolesList));
      metadata.add("authorization", `Bearer ${token}`);
    }
  } catch (error) {
    // If getting user info fails (e.g., invalid token), only add authorization
    // Let subsequent gRPC services handle authentication errors
    console.log("error:", error);
    metadata.add("authorization", `Bearer ${token}`);
  }

  return metadata;
}

function parseCookieToken(req: NextRequest): string | undefined {
  const cookieHeader = req.headers.get("cookie");
  if (!cookieHeader) {
    return undefined;
  }
  const cookies = parse(cookieHeader);
  return cookies.token;
}

async function invokeRPC(
  rule: RpcProxyRule,
  request: unknown,
  metadata?: grpc.Metadata,
): Promise<unknown> {
  const method = rule.method;
  return new Promise((resolve, reject) => {
    const callback = (err: grpc.ServiceError | null, response: unknown) => {
      if (err) return reject(err);
      resolve(response);
    };

    if (metadata) {
      method(request, metadata, callback);
    } else {
      method(request, callback);
    }
  });
}

function mapGrpcCodeToResponseCode(grpcCode?: number): ResponseCode {
  if (typeof grpcCode !== "number") {
    return ResponseCode.ERROR;
  }

  switch (grpcCode) {
    case grpc.status.OK:
      return ResponseCode.SUCCESS;
    case grpc.status.NOT_FOUND:
      return ResponseCode.NOT_FOUND;
    case grpc.status.INVALID_ARGUMENT:
    case grpc.status.OUT_OF_RANGE:
    case grpc.status.FAILED_PRECONDITION:
      return ResponseCode.BAD_REQUEST;
    case grpc.status.UNAUTHENTICATED:
      return ResponseCode.UNAUTHORIZED;
    case grpc.status.PERMISSION_DENIED:
      return ResponseCode.FORBIDDEN;
    default:
      return ResponseCode.ERROR;
  }
}

/**
 * Extract pure description from gRPC error message
 * gRPC error message format: "{code} {status_name}: {description}"
 * Example: "6 ALREADY_EXISTS: Username already exists" -> "Username already exists"
 */
function extractGrpcErrorMessage(serviceError: grpc.ServiceError): string {
  const message = serviceError.message || "Unknown error";

  // Try to extract the description part after the colon
  // Format: "6 ALREADY_EXISTS: Username already exists"
  const colonIndex = message.indexOf(":");
  if (colonIndex !== -1 && colonIndex < message.length - 1) {
    return message.substring(colonIndex + 1).trim();
  }

  // If no colon found, return original message
  return message;
}

function extractErrorDetails(
  serviceError: grpc.ServiceError,
): { reason: Reason; msg: string } | undefined {
  // Try to extract Details from metadata
  // In gRPC-JS, error details may be passed through metadata
  if (serviceError.metadata) {
    try {
      // Try to find Details in metadata
      // gRPC error details are usually passed through 'grpc-status-details-bin' key
      const detailsBin = serviceError.metadata.get("grpc-status-details-bin");
      if (detailsBin && detailsBin.length > 0) {
        // If binary data found, try to deserialize
        const buffer = Buffer.from(detailsBin[0] as string | Buffer);
        const details = Details.decode(new Uint8Array(buffer));
        const reasonValue = details.reason;
        // Map reason value to Reason type
        // In Reason enum, ERROR = 0
        const reasonKey = reasonValue === 0 ? "ERROR" : undefined;
        if (reasonKey) {
          return {
            reason: reasonKey as Reason,
            msg: details.msg || serviceError.message || "Unknown error",
          };
        }
      }
    } catch (error) {
      // If parsing fails, ignore error and continue with default handling
      console.warn("Failed to extract error details from gRPC error:", error);
    }
  }

  // If Details not found, return undefined
  return undefined;
}
