package org.tripsphere.poi.application.dto;

import java.util.List;
import org.tripsphere.poi.domain.model.GeoCoordinate;

public record SearchPoisNearbyQuery(
        GeoCoordinate center, double radiusMeters, int limit, List<String> categories, String adcode) {}
