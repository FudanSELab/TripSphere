import { Reason as ProtoReason } from "@/lib/grpc/gen/tripsphere/common/details_pb";

export enum ResponseCode {
  SUCCESS = "Success",
  ERROR = "Error",
  NOT_FOUND = "NotFound",
  BAD_REQUEST = "BadRequest",
  FORBIDDEN = "Forbidden",
  UNAUTHORIZED = "Unauthorized",
}

// Map of reason codes to their string representations
export const ReasonMap = {
  REASON_UNSPECIFIED: ProtoReason.REASON_UNSPECIFIED,
  REASON_ERROR: ProtoReason.REASON_ERROR,
  ERROR: "ERROR", // String version for HTTP responses
} as const;

export type Reason = keyof typeof ReasonMap;
