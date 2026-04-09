package org.tripsphere.user.infrastructure.adapter.inbound.grpc.advice;

import io.grpc.Status;
import lombok.extern.slf4j.Slf4j;
import net.devh.boot.grpc.server.advice.GrpcAdvice;
import net.devh.boot.grpc.server.advice.GrpcExceptionHandler;
import org.springframework.security.access.AccessDeniedException;
import org.springframework.security.core.AuthenticationException;
import org.tripsphere.user.application.exception.BusinessException;

/**
 * Global exception handler for gRPC services. Converts exceptions to appropriate gRPC Status
 * responses.
 */
@Slf4j
@GrpcAdvice
public class GrpcExceptionAdvice {

    /**
     * Handle all business exceptions. These are expected exceptions with predefined gRPC status
     * codes.
     */
    @GrpcExceptionHandler(BusinessException.class)
    public Status handleBusinessException(BusinessException e) {
        log.warn("Business exception: {}", e.getMessage());
        return e.toGrpcStatus();
    }

    /** Handle illegal argument exceptions (from validation). */
    @GrpcExceptionHandler(IllegalArgumentException.class)
    public Status handleIllegalArgumentException(IllegalArgumentException e) {
        log.warn("Illegal argument: {}", e.getMessage());
        return Status.INVALID_ARGUMENT.withDescription(e.getMessage());
    }

    /** Handle null pointer exceptions. */
    @GrpcExceptionHandler(NullPointerException.class)
    public Status handleNullPointerException(NullPointerException e) {
        log.error("Null pointer exception", e);
        return Status.INTERNAL.withDescription("Internal error: null reference");
    }

    @GrpcExceptionHandler(AccessDeniedException.class)
    public Status handleAccessDeniedException(AccessDeniedException e) {
        log.warn("Access denied: {}", e.getMessage());
        return Status.PERMISSION_DENIED.withDescription("Access denied");
    }

    @GrpcExceptionHandler(AuthenticationException.class)
    public Status handleAuthenticationException(AuthenticationException e) {
        log.warn("Authentication failed: {}", e.getMessage());
        return Status.UNAUTHENTICATED.withDescription("Authentication required");
    }

    /**
     * Handle all other unexpected exceptions. These are logged as errors and returned as INTERNAL
     * status.
     */
    @GrpcExceptionHandler(Exception.class)
    public Status handleException(Exception e) {
        log.error("Unexpected exception", e);
        return Status.INTERNAL.withDescription("An internal server error occurred");
    }
}
