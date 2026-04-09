package org.tripsphere.itinerary.application.dto;

import java.time.LocalDate;
import java.util.List;
import java.util.Map;
import org.tripsphere.itinerary.domain.model.DayPlan;
import org.tripsphere.itinerary.domain.model.ItinerarySummary;

public record CreateItineraryCommand(
        String userId,
        String title,
        String destinationPoiId,
        String destinationName,
        LocalDate startDate,
        LocalDate endDate,
        List<DayPlan> dayPlans,
        Map<String, Object> metadata,
        ItinerarySummary summary,
        String markdownContent) {}
