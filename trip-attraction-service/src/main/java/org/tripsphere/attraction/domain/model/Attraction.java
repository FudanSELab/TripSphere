package org.tripsphere.attraction.domain.model;

import java.util.List;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@Builder
@AllArgsConstructor
@NoArgsConstructor
public class Attraction {
    private String id;
    private String name;
    private String poiId;
    private GeoLocation location;
    private Address address;
    private String introduction;
    private List<String> tags;
    private List<String> images;
    private OpeningHours openingHours;
    private boolean temporarilyClosed;
    private TicketInfo ticketInfo;
    private RecommendTime recommendTime;
}
