package org.tripsphere.inventory.application.exception;

public class NotFoundException extends BusinessException {

    public NotFoundException(String message) {
        super(message, ErrorCode.NOT_FOUND);
    }

    public NotFoundException(String resourceType, String id) {
        super(resourceType + " with ID '" + id + "' not found", ErrorCode.NOT_FOUND);
    }
}
