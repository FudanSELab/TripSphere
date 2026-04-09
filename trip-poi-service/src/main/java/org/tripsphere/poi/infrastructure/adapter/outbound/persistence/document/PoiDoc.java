package org.tripsphere.poi.infrastructure.adapter.outbound.persistence.document;

import java.time.Instant;
import java.util.List;
import lombok.Data;
import org.springframework.data.annotation.CreatedDate;
import org.springframework.data.annotation.Id;
import org.springframework.data.annotation.LastModifiedDate;
import org.springframework.data.mongodb.core.geo.GeoJsonPoint;
import org.springframework.data.mongodb.core.index.GeoSpatialIndexType;
import org.springframework.data.mongodb.core.index.GeoSpatialIndexed;
import org.springframework.data.mongodb.core.mapping.Document;
import org.tripsphere.poi.domain.model.PoiAddress;

@Data
@Document(collection = "pois")
public class PoiDoc {

    @Id
    private String id;

    private String name;

    /** Location in WGS84 coordinate system. */
    @GeoSpatialIndexed(type = GeoSpatialIndexType.GEO_2DSPHERE)
    private GeoJsonPoint location;

    private PoiAddress address;
    private String adcode;
    private String amapId;
    private List<String> categories;
    private List<String> images;

    @CreatedDate
    private Instant createdAt;

    @LastModifiedDate
    private Instant updatedAt;
}
