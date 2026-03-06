package org.tripsphere.hotel.model;

import java.time.Instant;
import java.util.List;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;
import org.springframework.data.annotation.CreatedDate;
import org.springframework.data.annotation.Id;
import org.springframework.data.annotation.LastModifiedDate;
import org.springframework.data.mongodb.core.geo.GeoJsonPoint;
import org.springframework.data.mongodb.core.index.GeoSpatialIndexType;
import org.springframework.data.mongodb.core.index.GeoSpatialIndexed;
import org.springframework.data.mongodb.core.mapping.Document;

@Data
@Builder
@AllArgsConstructor
@NoArgsConstructor
@Document(collection = "hotels")
public class HotelDoc {
    @Id private String id;
    private String name;
    private String nameEn;
    private String poiId;

    /** Location in WGS84 coordinate system */
    @GeoSpatialIndexed(type = GeoSpatialIndexType.GEO_2DSPHERE)
    private GeoJsonPoint location;

    private Address address;
    private List<String> tags;
    private List<String> images;
    private HotelInformation information;
    private Money estimatedPrice;
    private HotelPolicy policy;
    private List<String> amenities;
    @CreatedDate private Instant createdAt;
    @LastModifiedDate private Instant updatedAt;
}
