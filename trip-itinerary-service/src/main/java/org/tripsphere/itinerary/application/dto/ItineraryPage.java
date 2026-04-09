package org.tripsphere.itinerary.application.dto;

import java.util.List;
import org.tripsphere.itinerary.domain.model.Itinerary;

public record ItineraryPage(List<Itinerary> items, String nextPageToken) {}
