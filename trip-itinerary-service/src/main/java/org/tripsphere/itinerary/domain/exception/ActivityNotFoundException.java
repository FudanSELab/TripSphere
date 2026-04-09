package org.tripsphere.itinerary.domain.exception;

public class ActivityNotFoundException extends ItineraryDomainException {

    public ActivityNotFoundException(String activityId) {
        super("Activity with ID '" + activityId + "' not found");
    }
}
