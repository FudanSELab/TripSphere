package org.tripsphere.itinerary.model;

import java.time.LocalTime;
import java.util.Map;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@Builder
@AllArgsConstructor
@NoArgsConstructor
public class ActivityDoc {
    private String id;
    private ActivityKind kind;
    private String title;
    private String description;
    private LocalTime startTime;
    private LocalTime endTime;
    private Money estimatedCost;
    private String attractionId;
    private String hotelId;
    private Map<String, Object> metadata;
    private GeoPointDoc location;
    private AddressDoc address;
    private String category;
}
