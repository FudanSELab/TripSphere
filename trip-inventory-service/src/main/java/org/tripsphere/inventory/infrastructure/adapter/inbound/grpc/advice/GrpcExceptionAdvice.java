package org.tripsphere.inventory.infrastructure.adapter.inbound.grpc.advice;

import io.grpc.Status;
import lombok.extern.slf4j.Slf4j;
import net.devh.boot.grpc.server.advice.GrpcAdvice;
import net.devh.boot.grpc.server.advice.GrpcExceptionHandler;
import org.tripsphere.inventory.application.exception.BusinessException;
import org.tripsphere.inventory.application.exception.ErrorCode;
import org.tripsphere.inventory.domain.exception.InsufficientStockException;
import org.tripsphere.inventory.domain.exception.InvalidLockStateException;
import org.tripsphere.inventory.domain.exception.InventoryDomainException;

@Slf4j
@GrpcAdvice
public class GrpcExceptionAdvice {

    @GrpcExceptionHandler(InsufficientStockException.class)
    public Status handleInsufficientStock(InsufficientStockException e) {
        log.warn("Insufficient stock: {}", e.getMessage());
        return Status.FAILED_PRECONDITION.withDescription(e.getMessage());
    }

    @GrpcExceptionHandler(InvalidLockStateException.class)
    public Status handleInvalidLockState(InvalidLockStateException e) {
        log.warn("Invalid lock state: {}", e.getMessage());
        return Status.FAILED_PRECONDITION.withDescription(e.getMessage());
    }

    @GrpcExceptionHandler(InventoryDomainException.class)
    public Status handleInventoryDomainException(InventoryDomainException e) {
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
            case INSUFFICIENT_INVENTORY -> Status.Code.FAILED_PRECONDITION;
            case INTERNAL -> Status.Code.INTERNAL;
        };
    }
}
