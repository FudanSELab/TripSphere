import { grpcClient } from "@/lib/grpc/client";
import {
  Attraction,
  FindAttractionByIdRequest,
  FindAttractionByIdResponse,
  FindAttractionsWithinRadiusRequest,
  FindAttractionsWithinRadiusResponse,
} from "@/lib/grpc/gen/tripsphere/attraction/attraction";
import {
  CreateReviewRequest,
  CreateReviewResponse,
  DeleteReviewRequest,
  DeleteReviewResponse,
  GetReviewByTargetIDRequest,
  GetReviewByTargetIDResponse,
  Review,
  UpdateReviewRequest,
  UpdateReviewResponse,
} from "@/lib/grpc/gen/tripsphere/review/review";
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
  // ============================================================================
  // User APIs
  // ============================================================================
  "POST /api/v1/users/register": RpcProxyRule<
    RegisterRequest,
    RegisterResponse,
    RegisterRequest,
    RegisterResponse
  >;
  "POST /api/v1/users/login": RpcProxyRule<
    LoginRequest,
    LoginResponse,
    LoginRequest,
    LoginResponse
  >;
  "GET /api/v1/users/current": RpcProxyRule<
    GetCurrentUserRequest,
    GetCurrentUserResponse,
    undefined,
    User
  >;

  // ============================================================================
  // Attraction APIs
  // ============================================================================
  "GET /api/v1/attractions/:id": RpcProxyRule<
    FindAttractionByIdRequest,
    FindAttractionByIdResponse,
    { id: string },
    Attraction
  >;
  "POST /api/v1/attractions/nearby": RpcProxyRule<
    FindAttractionsWithinRadiusRequest,
    FindAttractionsWithinRadiusResponse,
    FindAttractionsWithinRadiusRequest,
    Attraction[]
  >;

  // ============================================================================
  // Review APIs
  // ============================================================================
  "GET /api/v1/reviews": RpcProxyRule<
    GetReviewByTargetIDRequest,
    GetReviewByTargetIDResponse,
    {
      targetType: string;
      targetId: string;
      pageNumber: number;
      pageSize: number;
    },
    { reviews: Review[]; totalReviews: number }
  >;
  "POST /api/v1/reviews": RpcProxyRule<
    CreateReviewRequest,
    CreateReviewResponse,
    CreateReviewRequest,
    { id: string; status: boolean }
  >;
  "PUT /api/v1/reviews/:id": RpcProxyRule<
    UpdateReviewRequest,
    UpdateReviewResponse,
    UpdateReviewRequest,
    { status: boolean }
  >;
  "DELETE /api/v1/reviews/:id": RpcProxyRule<
    DeleteReviewRequest,
    DeleteReviewResponse,
    { id: string },
    { status: boolean }
  >;
}

export const grpcProxyMap: RpcProxyMap = {
  "POST /api/v1/users/register": {
    method: grpcClient.user.register.bind(grpcClient.user),
    buildRPCRequest: (request) => request,
    buildHttpResponse: (response) => response,
  },
  "POST /api/v1/users/login": {
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
        // Only use secure cookies when HTTPS is enabled
        // Set COOKIE_SECURE=true in production with HTTPS
        const isSecure = process.env.COOKIE_SECURE === "true";
        nextResponse.cookies.set("token", token, {
          httpOnly: true,
          secure: isSecure,
          sameSite: "lax",
          maxAge: 60 * 60 * 24 * 7, // 7 days
          path: "/",
        });
      }
      return nextResponse;
    },
  },
  "GET /api/v1/users/current": {
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
  "GET /api/v1/attractions/:id": {
    method: grpcClient.attraction.findAttractionById.bind(
      grpcClient.attraction,
    ),
    buildRPCRequest: (request: { id: string }) =>
      FindAttractionByIdRequest.create({ id: request.id }),
    buildHttpResponse: (response: FindAttractionByIdResponse) => {
      if (!response.attraction) {
        throw new Error("Attraction not found in response");
      }
      return response.attraction;
    },
  },
  "POST /api/v1/attractions/nearby": {
    method: grpcClient.attraction.findAttractionsWithinRadius.bind(
      grpcClient.attraction,
    ),
    buildRPCRequest: (request: FindAttractionsWithinRadiusRequest) =>
      FindAttractionsWithinRadiusRequest.create(request),
    buildHttpResponse: (response: FindAttractionsWithinRadiusResponse) => {
      return response.content;
    },
  },
  "GET /api/v1/reviews": {
    method: grpcClient.review.getReviewByTargetId.bind(grpcClient.review),
    buildRPCRequest: (request: {
      targetType: string;
      targetId: string;
      pageNumber: number;
      pageSize: number;
    }) =>
      GetReviewByTargetIDRequest.create({
        targetType: request.targetType,
        targetId: request.targetId,
        pageNumber: request.pageNumber || 1,
        pageSize: request.pageSize || 20,
      }),
    buildHttpResponse: (response: GetReviewByTargetIDResponse) => ({
      reviews: response.reviews,
      totalReviews: response.totalReviews,
    }),
  },
  "POST /api/v1/reviews": {
    method: grpcClient.review.createReview.bind(grpcClient.review),
    buildRPCRequest: (request: CreateReviewRequest) =>
      CreateReviewRequest.create(request),
    buildHttpResponse: (response: CreateReviewResponse) => ({
      id: response.id,
      status: response.status,
    }),
  },
  "PUT /api/v1/reviews/:id": {
    method: grpcClient.review.updateReview.bind(grpcClient.review),
    buildRPCRequest: (request: UpdateReviewRequest) =>
      UpdateReviewRequest.create(request),
    buildHttpResponse: (response: UpdateReviewResponse) => ({
      status: response.status,
    }),
  },
  "DELETE /api/v1/reviews/:id": {
    method: grpcClient.review.deleteReview.bind(grpcClient.review),
    buildRPCRequest: (request: { id: string }) =>
      DeleteReviewRequest.create({ id: request.id }),
    buildHttpResponse: (response: DeleteReviewResponse) => ({
      status: response.status,
    }),
  },
};
