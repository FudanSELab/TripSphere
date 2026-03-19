package org.tripsphere.inventory.application.exception;

public class InvalidArgumentException extends BusinessException {

    public InvalidArgumentException(String message) {
        super(message, ErrorCode.INVALID_ARGUMENT);
    }

    public static InvalidArgumentException required(String fieldName) {
        return new InvalidArgumentException(fieldName + " is required");
    }

    public static InvalidArgumentException invalid(String fieldName, String reason) {
        return new InvalidArgumentException(fieldName + " is invalid: " + reason);
    }
}
