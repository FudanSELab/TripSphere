package org.tripsphere.itinerary.domain.exception;

public class ItineraryDomainException extends RuntimeException {

    public ItineraryDomainException(String message) {
        super(message);
    }

    public ItineraryDomainException(String message, Throwable cause) {
        super(message, cause);
    }
}
