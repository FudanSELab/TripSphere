package org.tripsphere.itinerary.infrastructure.adapter.outbound.persistence.document;

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
public class ActivityDocument {
    private String id;
    private String kind;
    private String title;
    private String description;
    private LocalTime startTime;
    private LocalTime endTime;
    private MoneyDocument estimatedCost;
    private String attractionId;
    private String hotelId;
    private Map<String, Object> metadata;
    private GeoPointDocument location;
    private AddressDocument address;
    private String category;
}
