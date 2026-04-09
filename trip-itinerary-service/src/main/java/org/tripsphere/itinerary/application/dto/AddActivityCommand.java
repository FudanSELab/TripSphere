package org.tripsphere.itinerary.application.dto;

import org.tripsphere.itinerary.domain.model.Activity;

public record AddActivityCommand(String itineraryId, String dayPlanId, Activity activity, int insertIndex) {}
