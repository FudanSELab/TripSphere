import { grpcClient } from "@/lib/grpc/client";
import {
  GetCurrentUserRequest,
  GetCurrentUserResponse,
  LoginRequest,
  LoginResponse,
  RegisterRequest,
  RegisterResponse,
} from "@/lib/grpc/gen/tripsphere/user/user";
import { ResponseData } from "@/lib/requests";
import { User } from "@/lib/types";
import type { NextRequest } from "next/server";
import { NextResponse } from "next/server";

export type HttpResponseHook<HttpResponseType = unknown> = (ctx: {
  req: NextRequest;
  httpResponse: ResponseData<HttpResponseType>;
}) => NextResponse | void;

export interface RpcProxyRule<
  RPCRequestType = unknown,
  RPCResponseType = unknown,
  HttpRequestType = unknown,
  HttpResponseType = unknown,
> {
  // eslint-disable-next-line @typescript-eslint/no-unsafe-function-type
  method: Function;
  buildRPCRequest: (request: HttpRequestType) => RPCRequestType;
  buildHttpResponse: (response: RPCResponseType) => HttpResponseType;
  httpResponseHook?: HttpResponseHook;
}

export interface RpcProxyMap {
  "POST /api/v1/user/register": RpcProxyRule<
    RegisterRequest,
    RegisterResponse,
    RegisterRequest,
    RegisterResponse
  >;
  "POST /api/v1/user/login": RpcProxyRule<
    LoginRequest,
    LoginResponse,
    LoginRequest,
    LoginResponse
  >;
  "POST /api/v1/user/get-current-user": RpcProxyRule<
    GetCurrentUserRequest,
    GetCurrentUserResponse,
    undefined,
    User
  >;
}

export const grpcProxyMap: RpcProxyMap = {
  "POST /api/v1/user/register": {
    method: grpcClient.user.register.bind(grpcClient.user),
    buildRPCRequest: (request) => request,
    buildHttpResponse: (response) => response,
  },
  "POST /api/v1/user/login": {
    method: grpcClient.user.login.bind(grpcClient.user),
    buildRPCRequest: (request) => request,
    buildHttpResponse: (response) => response,
    httpResponseHook: ({ httpResponse }) => {
      const loginData = httpResponse.data as LoginResponse;
      const nextResponse = NextResponse.json({
        ...httpResponse,
        data: { user: loginData?.user },
      });
      const token = loginData?.token;
      if (token) {
        nextResponse.cookies.set("token", token, {
          httpOnly: true,
          secure: process.env.NODE_ENV === "production",
          sameSite: "lax",
          maxAge: 60 * 60 * 24 * 7, // 7 days
          path: "/",
        });
      }
      return nextResponse;
    },
  },
  "POST /api/v1/user/get-current-user": {
    method: grpcClient.user.getCurrentUser.bind(grpcClient.user),
    buildRPCRequest: () => GetCurrentUserRequest.create({}),
    buildHttpResponse: (response: GetCurrentUserResponse) => {
      // Convert gRPC User to frontend User type
      const grpcUser = response.user;
      if (!grpcUser) {
        throw new Error("User not found in response");
      }

      // Note: gRPC User only has id, username, roles
      // avatar and createdAt are optional in frontend User type
      const user: User = {
        id: grpcUser.id,
        username: grpcUser.username,
        roles: grpcUser.roles,
        // avatar and createdAt not provided by gRPC User
      };

      return user;
    },
  },
};
