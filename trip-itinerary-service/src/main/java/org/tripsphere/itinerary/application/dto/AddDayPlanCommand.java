package org.tripsphere.itinerary.application.dto;

import org.tripsphere.itinerary.domain.model.DayPlan;

public record AddDayPlanCommand(String itineraryId, DayPlan dayPlan) {}
