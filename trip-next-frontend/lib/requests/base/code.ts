import { ReasonMap } from "@/lib/grpc/gen/common/details_pb";


export enum ResponseCode {
    SUCCESS = 'Success',
    ERROR = 'Error',
    NOT_FOUND = 'NotFound',
    BAD_REQUEST = 'BadRequest',
    FORBIDDEN = 'Forbidden',
    UNAUTHORIZED = 'Unauthorized',
}

export type Reason = keyof ReasonMap
