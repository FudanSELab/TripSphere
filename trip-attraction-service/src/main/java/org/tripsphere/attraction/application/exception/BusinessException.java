package org.tripsphere.attraction.application.exception;

import io.grpc.Status;
import lombok.Getter;

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

    public Status toGrpcStatus() {
        return Status.fromCode(statusCode).withDescription(getMessage());
    }
}
