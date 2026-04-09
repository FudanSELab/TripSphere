package org.tripsphere.poi.application.dto;

import java.util.List;
import org.tripsphere.poi.domain.model.GeoCoordinate;
import org.tripsphere.poi.domain.model.PoiAddress;

public record CreatePoiCommand(
        String name,
        GeoCoordinate location,
        PoiAddress address,
        String adcode,
        String amapId,
        List<String> categories,
        List<String> images) {}
