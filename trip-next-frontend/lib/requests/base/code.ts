import { Reason as PbReason } from "@/lib/grpc/gen/tripsphere/common/details";

export enum ResponseCode {
  SUCCESS = "Success",
  ERROR = "Error",
  NOT_FOUND = "NotFound",
  BAD_REQUEST = "BadRequest",
  FORBIDDEN = "Forbidden",
  UNAUTHORIZED = "Unauthorized",
}

export const ReasonMap = {
  REASON_UNSPECIFIED: PbReason.REASON_UNSPECIFIED,
  REASON_ERROR: PbReason.REASON_ERROR,
};

export type Reason = keyof typeof ReasonMap;
