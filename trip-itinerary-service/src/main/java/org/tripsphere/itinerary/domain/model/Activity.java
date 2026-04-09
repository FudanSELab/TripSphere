package org.tripsphere.itinerary.domain.model;

import com.github.f4b6a3.uuid.UuidCreator;
import java.time.LocalTime;
import java.util.Map;
import lombok.Builder;
import lombok.Getter;

@Getter
@Builder
public class Activity {
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
    private GeoPoint location;
    private Address address;
    private String category;

    public void ensureId() {
        if (id == null || id.isEmpty()) {
            id = UuidCreator.getTimeOrderedEpoch().toString();
        }
    }
}
