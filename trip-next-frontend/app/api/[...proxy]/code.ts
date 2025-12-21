import * as grpc from "@grpc/grpc-js";

export function mapGrpcCodeToHttp(code: number): number {
  switch (code) {
    case grpc.status.INVALID_ARGUMENT:
    case grpc.status.OUT_OF_RANGE:
    case grpc.status.FAILED_PRECONDITION:
      return 400;
    case grpc.status.UNAUTHENTICATED:
      return 401;
    case grpc.status.PERMISSION_DENIED:
      return 403;
    case grpc.status.NOT_FOUND:
      return 404;
    case grpc.status.ABORTED:
    case grpc.status.ALREADY_EXISTS:
      return 409;
    case grpc.status.UNAVAILABLE:
      return 503;
    case grpc.status.DEADLINE_EXCEEDED:
      return 504;
    default:
      return 502;
  }
}
