package org.tripsphere.user.application.exception;

import io.grpc.Status;
import lombok.Getter;

/**
 * Base exception for all business exceptions. Subclasses should define their own gRPC status code.
 */
@Getter
public abstract class BusinessException extends RuntimeException {

    private final Status.Code statusCode;

    protected BusinessException(String message, Status.Code statusCode) {
        super(message);
        this.statusCode = statusCode;
    }

    protected BusinessException(String message, Throwable cause, Status.Code statusCode) {
        super(message, cause);
        this.statusCode = statusCode;
    }

    /** Convert this exception to a gRPC Status. */
    public Status toGrpcStatus() {
        return Status.fromCode(statusCode).withDescription(getMessage());
    }
}
