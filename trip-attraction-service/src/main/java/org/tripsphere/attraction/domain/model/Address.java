package org.tripsphere.attraction.domain.model;

import java.util.stream.Collectors;
import java.util.stream.Stream;

public record Address(String province, String city, String district, String detailed) {
    public Address {
        province = (province == null) ? "" : province.trim();
        city = (city == null) ? "" : city.trim();
        district = (district == null) ? "" : district.trim();
        detailed = (detailed == null) ? "" : detailed.trim();
    }

    public String fullAddress() {
        return Stream.of(province, city, district, detailed)
                .filter(s -> !s.isEmpty())
                .collect(Collectors.joining(""));
    }
}
