package org.tripsphere.hotel.domain.model;

import java.time.Instant;
import java.util.List;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@Builder
@AllArgsConstructor
@NoArgsConstructor
public class Hotel {
    private String id;
    private String name;
    private String nameEn;
    private String poiId;
    private GeoLocation location;
    private Address address;
    private List<String> tags;
    private List<String> images;
    private HotelInformation information;
    private Money estimatedPrice;
    private HotelPolicy policy;
    private List<String> amenities;
    private Instant createdAt;
}
