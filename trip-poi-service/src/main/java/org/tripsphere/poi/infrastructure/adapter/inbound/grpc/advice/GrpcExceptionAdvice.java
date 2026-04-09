package org.tripsphere.poi.infrastructure.adapter.inbound.grpc.advice;

import io.grpc.Status;
import lombok.extern.slf4j.Slf4j;
import net.devh.boot.grpc.server.advice.GrpcAdvice;
import net.devh.boot.grpc.server.advice.GrpcExceptionHandler;
import org.tripsphere.poi.application.exception.BusinessException;
import org.tripsphere.poi.application.exception.ErrorCode;

@Slf4j
@GrpcAdvice
public class GrpcExceptionAdvice {

    @GrpcExceptionHandler(BusinessException.class)
    public Status handleBusinessException(BusinessException e) {
        log.warn("Business exception: {}", e.getMessage());
        return Status.fromCode(mapToGrpcCode(e.getErrorCode())).withDescription(e.getMessage());
    }

    @GrpcExceptionHandler(IllegalArgumentException.class)
    public Status handleIllegalArgumentException(IllegalArgumentException e) {
        log.warn("Illegal argument: {}", e.getMessage());
        return Status.INVALID_ARGUMENT.withDescription(e.getMessage());
    }

    @GrpcExceptionHandler(NullPointerException.class)
    public Status handleNullPointerException(NullPointerException e) {
        log.error("Null pointer exception", e);
        return Status.INTERNAL.withDescription("Internal error: null reference");
    }

    @GrpcExceptionHandler(Exception.class)
    public Status handleException(Exception e) {
        log.error("Unexpected exception in gRPC service", e);
        return Status.INTERNAL.withDescription("Internal server error: " + e.getMessage());
    }

    private Status.Code mapToGrpcCode(ErrorCode errorCode) {
        return switch (errorCode) {
            case NOT_FOUND -> Status.Code.NOT_FOUND;
            case INVALID_ARGUMENT -> Status.Code.INVALID_ARGUMENT;
            case ALREADY_EXISTS -> Status.Code.ALREADY_EXISTS;
            case INTERNAL -> Status.Code.INTERNAL;
        };
    }
}
