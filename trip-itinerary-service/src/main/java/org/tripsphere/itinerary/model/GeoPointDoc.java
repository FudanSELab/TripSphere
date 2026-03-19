package org.tripsphere.itinerary.model;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;
import org.springframework.data.mongodb.core.mapping.Field;

@Data
@Builder
@AllArgsConstructor
@NoArgsConstructor
public class GeoPointDoc {
    private Double longitude;
    private Double latitude;

    /**
     * Legacy itineraries only: {@code location.name} in Mongo. Not written on new saves.
     */
    private String name;

    /**
     * Legacy itineraries only: flat {@code location.address} string in Mongo. Not written on new saves.
     */
    @Field("address")
    private String lineAddress;
}
