package org.tripsphere.itinerary.infrastructure.adapter.outbound.persistence.document;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;
import org.springframework.data.mongodb.core.mapping.Field;

@Data
@Builder
@AllArgsConstructor
@NoArgsConstructor
public class GeoPointDocument {
    private Double longitude;
    private Double latitude;
    private String name;

    @Field("address")
    private String lineAddress;
}
