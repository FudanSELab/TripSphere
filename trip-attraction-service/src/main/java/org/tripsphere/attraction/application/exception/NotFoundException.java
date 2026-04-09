package org.tripsphere.attraction.application.exception;

import io.grpc.Status;

public class NotFoundException extends BusinessException {

    public NotFoundException(String message) {
        super(message, Status.Code.NOT_FOUND);
    }

    public NotFoundException(String resourceType, String id) {
        super(resourceType + " with ID '" + id + "' not found", Status.Code.NOT_FOUND);
    }
}
