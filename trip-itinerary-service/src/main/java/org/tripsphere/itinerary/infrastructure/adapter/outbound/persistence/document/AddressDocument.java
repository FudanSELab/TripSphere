package org.tripsphere.itinerary.infrastructure.adapter.outbound.persistence.document;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@Builder
@AllArgsConstructor
@NoArgsConstructor
public class AddressDocument {
    private String province;
    private String city;
    private String district;
    private String detailed;
}
