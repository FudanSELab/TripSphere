package org.tripsphere.itinerary.model;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@Builder
@AllArgsConstructor
@NoArgsConstructor
public class AddressDoc {
    private String province;
    private String city;
    private String district;
    private String detailed;
}
