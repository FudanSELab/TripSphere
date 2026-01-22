import { grpcClient } from "@/lib/grpc/client";

// Attraction types
import {
  FindAttractionByIdRequest,
  FindAttractionByIdResponse,
  FindAttractionsWithinRadiusPageRequest,
  FindAttractionsWithinRadiusPageResponse,
} from "@/lib/grpc/gen/tripsphere/attraction/attraction";

// User types
import {
  GetCurrentUserRequest,
  GetCurrentUserResponse,
  LoginRequest,
  LoginResponse,
  RegisterRequest,
  RegisterResponse,
} from "@/lib/grpc/gen/tripsphere/user/user";

import { ResponseData } from "@/lib/requests";
import type { Attraction, User } from "@/lib/types";
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
  // User APIs
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

  // Attraction APIs
  "POST /api/v1/attraction/find-by-id": RpcProxyRule<
    FindAttractionByIdRequest,
    FindAttractionByIdResponse,
    { id: string },
    Attraction
  >;
  "POST /api/v1/attraction/search": RpcProxyRule<
    FindAttractionsWithinRadiusPageRequest,
    FindAttractionsWithinRadiusPageResponse,
    {
      location: { lng: number; lat: number };
      radiusKm: number;
      page: number;
      pageSize: number;
      name?: string;
      tags?: string[];
    },
    {
      attractions: Attraction[];
      totalPages: number;
      totalElements: number;
      currentPage: number;
      pageSize: number;
    }
  >;
}

// Helper function to convert gRPC Attraction to frontend Attraction
function convertGrpcAttractionToFrontend(
  grpcAttraction: import("@/lib/grpc/gen/tripsphere/attraction/attraction").Attraction,
): Attraction {
  return {
    id: grpcAttraction.id,
    name: grpcAttraction.name,
    description: grpcAttraction.introduction, // Map introduction to description
    address: grpcAttraction.address || {
      country: "",
      province: "",
      city: "",
      county: "",
      district: "",
      street: "",
    },
    location: {
      lng: grpcAttraction.location?.longitude || 0,
      lat: grpcAttraction.location?.latitude || 0,
    },
    category: grpcAttraction.tags?.[0] || "Attraction", // Use first tag as category
    images: grpcAttraction.images,
    tags: grpcAttraction.tags,
  };
}

export const grpcProxyMap: RpcProxyMap = {
  // ============================================================================
  // User APIs
  // ============================================================================
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

  // ============================================================================
  // Attraction APIs
  // ============================================================================
  "POST /api/v1/attraction/find-by-id": {
    method: grpcClient.attraction.findAttractionById.bind(
      grpcClient.attraction,
    ),
    buildRPCRequest: (request: { id: string }) =>
      FindAttractionByIdRequest.create({ id: request.id }),
    buildHttpResponse: (response: FindAttractionByIdResponse) => {
      if (!response.attraction) {
        throw new Error("Attraction not found");
      }
      return convertGrpcAttractionToFrontend(response.attraction);
    },
  },

  "POST /api/v1/attraction/search": {
    method: grpcClient.attraction.findAttractionsWithinRadiusPage.bind(
      grpcClient.attraction,
    ),
    buildRPCRequest: (request: {
      location: { lng: number; lat: number };
      radiusKm: number;
      page: number;
      pageSize: number;
      name?: string;
      tags?: string[];
    }) =>
      FindAttractionsWithinRadiusPageRequest.create({
        location: {
          longitude: request.location.lng,
          latitude: request.location.lat,
        },
        radiusKm: request.radiusKm,
        number: request.page,
        size: request.pageSize,
        name: request.name || "",
        tags: request.tags || [],
      }),
    buildHttpResponse: (response: FindAttractionsWithinRadiusPageResponse) => {
      const page = response.attractionPage;
      if (!page) {
        return {
          attractions: [],
          totalPages: 0,
          totalElements: 0,
          currentPage: 0,
          pageSize: 0,
        };
      }

      return {
        attractions: page.content.map(convertGrpcAttractionToFrontend),
        totalPages: page.totalPages,
        totalElements: Number(page.totalElements),
        currentPage: page.number,
        pageSize: page.size,
      };
    },
  },
};
