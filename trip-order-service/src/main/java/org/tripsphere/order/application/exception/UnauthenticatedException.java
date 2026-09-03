package org.tripsphere.order.application.exception;

public class UnauthenticatedException extends BusinessException {

    public UnauthenticatedException(String message) {
        super(message, ErrorCode.UNAUTHENTICATED);
    }

    public static UnauthenticatedException authenticationRequired() {
        return new UnauthenticatedException("Authentication required");
    }
}
