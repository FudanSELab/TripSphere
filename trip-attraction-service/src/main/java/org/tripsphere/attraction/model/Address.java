package org.tripsphere.attraction.model;

import lombok.Data;

@Data
public class Address {
    private String country;
    private String province;
    private String city;
    private String county;
    private String district;
    private String street;
}
