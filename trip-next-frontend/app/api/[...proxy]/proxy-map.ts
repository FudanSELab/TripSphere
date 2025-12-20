import type { NextRequest } from 'next/server'
import { NextResponse } from 'next/server'
import { grpcClient } from '../../../lib/grpc/client'
import {
  LoginRequest,
  LoginResponse,
  RegisterRequest,
  RegisterResponse,
} from '../../../lib/grpc/gen/user/user_pb'
import { createRequestFromObject } from '@/lib/grpc/utils'
import { ResponseData } from '@/lib/requests'

export type HttpResponseHook<HttpResponseType = any> = (ctx: {
  req: NextRequest
  httpResponse: ResponseData<HttpResponseType>
}) => NextResponse | void

export interface RpcProxyRule<RPCRequestType = any, RPCResponseType = any, HttpRequestType = any, HttpResponseType = any> {
  method: Function,
  buildRPCRequest: (request: HttpRequestType) => RPCRequestType
  buildHttpResponse: (response: RPCResponseType) => HttpResponseType
  httpResponseHook?: HttpResponseHook
}

export interface RpcProxyMap {
  "POST /api/user/register": RpcProxyRule<RegisterRequest, RegisterResponse, RegisterRequest.AsObject, RegisterResponse.AsObject>
  "POST /api/user/login": RpcProxyRule<LoginRequest, LoginResponse,  LoginRequest.AsObject, LoginResponse.AsObject>
}

export const grpcProxyMap: RpcProxyMap = {
  "POST /api/user/register": {
    method: grpcClient.user.register.bind(grpcClient.user),
    buildRPCRequest: request => createRequestFromObject(RegisterRequest, request) ,
    buildHttpResponse: response => RegisterResponse.toObject(false, response),
  },
  "POST /api/user/login": {
    method: grpcClient.user.login.bind(grpcClient.user),
    buildRPCRequest: request => createRequestFromObject(LoginRequest, request) ,
    buildHttpResponse: response => LoginResponse.toObject(false, response),
    httpResponseHook: ({ httpResponse }) => {
      const nextResponse = NextResponse.json({
        ...httpResponse,
        data: { user: httpResponse.data.user }
      })
      const token = httpResponse.data?.token
      if (token) {
        nextResponse.cookies.set('token', token, {
          httpOnly: true,
          secure: process.env.NODE_ENV === 'production',
          sameSite: 'lax',
          maxAge: 60 * 60 * 24 * 7, // 7 days
          path: '/',
        })
      }
      return nextResponse
    },
  }
}
