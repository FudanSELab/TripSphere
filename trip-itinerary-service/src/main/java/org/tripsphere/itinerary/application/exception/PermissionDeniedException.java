package org.tripsphere.itinerary.application.exception;

import io.grpc.Status;

public class PermissionDeniedException extends BusinessException {

    public PermissionDeniedException(String message) {
        super(message, Status.Code.PERMISSION_DENIED);
    }

    public static PermissionDeniedException notOwner() {
        return new PermissionDeniedException("You don't have permission to access this resource");
    }
}
