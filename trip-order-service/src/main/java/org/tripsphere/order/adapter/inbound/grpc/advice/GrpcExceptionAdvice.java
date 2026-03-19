package org.tripsphere.order.adapter.inbound.grpc.advice;

import io.grpc.Status;
import lombok.extern.slf4j.Slf4j;
import net.devh.boot.grpc.server.advice.GrpcAdvice;
import net.devh.boot.grpc.server.advice.GrpcExceptionHandler;
import org.tripsphere.order.application.exception.BusinessException;
import org.tripsphere.order.application.exception.ErrorCode;
import org.tripsphere.order.domain.exception.InvalidOrderStateException;
import org.tripsphere.order.domain.exception.OrderDomainException;

@Slf4j
@GrpcAdvice
public class GrpcExceptionAdvice {

    @GrpcExceptionHandler(InvalidOrderStateException.class)
    public Status handleInvalidOrderState(InvalidOrderStateException e) {
        log.warn("Invalid order state: {}", e.getMessage());
        return Status.FAILED_PRECONDITION.withDescription(e.getMessage());
    }

    @GrpcExceptionHandler(OrderDomainException.class)
    public Status handleOrderDomainException(OrderDomainException e) {
        log.warn("Domain exception: {}", e.getMessage());
        return Status.FAILED_PRECONDITION.withDescription(e.getMessage());
    }

    @GrpcExceptionHandler(BusinessException.class)
    public Status handleBusinessException(BusinessException e) {
        log.warn("Business exception: {}", e.getMessage());
        Status.Code grpcCode = mapToGrpcCode(e.getErrorCode());
        return Status.fromCode(grpcCode).withDescription(e.getMessage());
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
            case ORDER_STATE_CONFLICT -> Status.Code.FAILED_PRECONDITION;
            case INTERNAL -> Status.Code.INTERNAL;
        };
    }
}
