package org.tripsphere.itinerary.application.dto;

import java.time.LocalDate;
import org.tripsphere.itinerary.domain.model.ItinerarySummary;

public record UpdateItineraryCommand(
        String id,
        String title,
        LocalDate startDate,
        LocalDate endDate,
        String destinationName,
        String markdownContent,
        ItinerarySummary summary) {}
