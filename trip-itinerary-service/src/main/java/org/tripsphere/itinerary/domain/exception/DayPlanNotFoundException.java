package org.tripsphere.itinerary.domain.exception;

public class DayPlanNotFoundException extends ItineraryDomainException {

    public DayPlanNotFoundException(String dayPlanId) {
        super("DayPlan with ID '" + dayPlanId + "' not found");
    }
}
