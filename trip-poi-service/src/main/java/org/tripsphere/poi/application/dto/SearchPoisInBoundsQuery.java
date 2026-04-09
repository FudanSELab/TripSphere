package org.tripsphere.poi.application.dto;

import java.util.List;
import org.tripsphere.poi.domain.model.GeoCoordinate;

public record SearchPoisInBoundsQuery(
        GeoCoordinate southWest, GeoCoordinate northEast, int limit, List<String> categories, String adcode) {}
