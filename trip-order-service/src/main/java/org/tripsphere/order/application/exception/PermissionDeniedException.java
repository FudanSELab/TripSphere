package org.tripsphere.order.application.exception;

public class PermissionDeniedException extends BusinessException {

    public PermissionDeniedException(String message) {
        super(message, ErrorCode.PERMISSION_DENIED);
    }

    public static PermissionDeniedException notOwner() {
        return new PermissionDeniedException("You don't have permission to access this order");
    }
}
