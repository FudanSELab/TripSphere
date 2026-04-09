package org.tripsphere.poi.domain.model;

import java.time.Instant;
import java.util.List;
import lombok.Builder;
import lombok.Getter;

/** Aggregate root representing a Point of Interest. Location is always stored in WGS84. */
@Getter
@Builder
public class Poi {

    private String id;
    private String name;
    private GeoCoordinate location;
    private PoiAddress address;
    private String adcode;
    private String amapId;
    private List<String> categories;
    private List<String> images;
    private Instant createdAt;
    private Instant updatedAt;

    public static Poi create(
            String id,
            String name,
            GeoCoordinate location,
            PoiAddress address,
            String adcode,
            String amapId,
            List<String> categories,
            List<String> images) {
        return Poi.builder()
                .id(id)
                .name(name)
                .location(location)
                .address(address)
                .adcode(adcode)
                .amapId(amapId)
                .categories(categories != null ? List.copyOf(categories) : List.of())
                .images(images != null ? List.copyOf(images) : List.of())
                .build();
    }
}
