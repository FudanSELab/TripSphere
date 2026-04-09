package org.tripsphere.itinerary.application.exception;

import io.grpc.Status;

public class UnauthenticatedException extends BusinessException {

    public UnauthenticatedException(String message) {
        super(message, Status.Code.UNAUTHENTICATED);
    }

    public static UnauthenticatedException authenticationRequired() {
        return new UnauthenticatedException("Authentication required");
    }
}
