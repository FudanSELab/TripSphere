package org.tripsphere.itinerary.application.dto;

public record ListItinerariesQuery(String userId, int pageSize, String pageToken) {}
