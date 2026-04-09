package org.tripsphere.attraction.infrastructure.adapter.outbound.persistence.document;

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
import org.tripsphere.attraction.domain.model.Address;
import org.tripsphere.attraction.domain.model.OpeningHours;
import org.tripsphere.attraction.domain.model.RecommendTime;
import org.tripsphere.attraction.domain.model.TicketInfo;

@Data
@Builder
@AllArgsConstructor
@NoArgsConstructor
@Document(collection = "attractions")
public class AttractionDocument {
    @Id
    private String id;

    private String name;
    private String poiId;

    /** Location in WGS84 coordinate system */
    @GeoSpatialIndexed(type = GeoSpatialIndexType.GEO_2DSPHERE)
    private GeoJsonPoint location;

    private Address address;
    private String introduction;
    private List<String> tags;
    private List<String> images;
    private OpeningHours openingHours;
    private boolean temporarilyClosed;
    private TicketInfo ticketInfo;
    private RecommendTime recommendTime;

    @CreatedDate
    private Instant createdAt;

    @LastModifiedDate
    private Instant updatedAt;
}
