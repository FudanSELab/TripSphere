package org.tripsphere.itinerary.application.exception;

import io.grpc.Status;

public class AlreadyExistsException extends BusinessException {

    public AlreadyExistsException(String message) {
        super(message, Status.Code.ALREADY_EXISTS);
    }

    public AlreadyExistsException(String resourceType, String id) {
        super(resourceType + " with ID '" + id + "' already exists", Status.Code.ALREADY_EXISTS);
    }
}
