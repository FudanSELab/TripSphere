package org.tripsphere.product.adapter.inbound.grpc.advice;

import io.grpc.Status;
import lombok.extern.slf4j.Slf4j;
import net.devh.boot.grpc.server.advice.GrpcAdvice;
import net.devh.boot.grpc.server.advice.GrpcExceptionHandler;
import org.tripsphere.product.application.exception.BusinessException;
import org.tripsphere.product.application.exception.ErrorCode;
import org.tripsphere.product.domain.exception.DuplicateSkuNameException;
import org.tripsphere.product.domain.exception.InvalidSkuStateException;
import org.tripsphere.product.domain.exception.InvalidSpuStateException;
import org.tripsphere.product.domain.exception.ProductDomainException;

@Slf4j
@GrpcAdvice
public class GrpcExceptionAdvice {

    @GrpcExceptionHandler(InvalidSpuStateException.class)
    public Status handleInvalidSpuState(InvalidSpuStateException e) {
        log.warn("Invalid SPU state: {}", e.getMessage());
        return Status.FAILED_PRECONDITION.withDescription(e.getMessage());
    }

    @GrpcExceptionHandler(InvalidSkuStateException.class)
    public Status handleInvalidSkuState(InvalidSkuStateException e) {
        log.warn("Invalid SKU state: {}", e.getMessage());
        return Status.FAILED_PRECONDITION.withDescription(e.getMessage());
    }

    @GrpcExceptionHandler(DuplicateSkuNameException.class)
    public Status handleDuplicateSkuName(DuplicateSkuNameException e) {
        log.warn("Duplicate SKU name: {}", e.getMessage());
        return Status.ALREADY_EXISTS.withDescription(e.getMessage());
    }

    @GrpcExceptionHandler(ProductDomainException.class)
    public Status handleProductDomainException(ProductDomainException e) {
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
            case INTERNAL -> Status.Code.INTERNAL;
        };
    }
}
