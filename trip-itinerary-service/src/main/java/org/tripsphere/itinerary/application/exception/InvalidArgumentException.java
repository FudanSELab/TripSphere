package org.tripsphere.itinerary.application.exception;

import io.grpc.Status;

public class InvalidArgumentException extends BusinessException {

    public InvalidArgumentException(String message) {
        super(message, Status.Code.INVALID_ARGUMENT);
    }

    public static InvalidArgumentException required(String fieldName) {
        return new InvalidArgumentException("Field '" + fieldName + "' is required");
    }

    public static InvalidArgumentException invalid(String fieldName, String reason) {
        return new InvalidArgumentException("Field '" + fieldName + "' is invalid: " + reason);
    }
}
