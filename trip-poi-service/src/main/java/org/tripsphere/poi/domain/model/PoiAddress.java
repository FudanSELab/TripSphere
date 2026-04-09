package org.tripsphere.poi.domain.model;

import java.util.stream.Collectors;
import java.util.stream.Stream;

/** Value object representing a Chinese address. */
public record PoiAddress(String province, String city, String district, String detailed) {

    public PoiAddress {
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
