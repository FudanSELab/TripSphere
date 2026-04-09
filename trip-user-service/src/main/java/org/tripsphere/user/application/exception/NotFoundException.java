package org.tripsphere.user.application.exception;

import io.grpc.Status;

/** Exception thrown when a requested resource is not found. */
public class NotFoundException extends BusinessException {

    public NotFoundException(String message) {
        super(message, Status.Code.NOT_FOUND);
    }

    public NotFoundException(String resourceType, String identifier) {
        super(resourceType + " '" + identifier + "' not found", Status.Code.NOT_FOUND);
    }
}
