package org.tripsphere.poi.infrastructure.adapter.inbound.grpc.mapper;

import java.util.List;
import org.mapstruct.CollectionMappingStrategy;
import org.mapstruct.Mapper;
import org.mapstruct.MappingConstants;
import org.mapstruct.NullValueCheckStrategy;
import org.mapstruct.ReportingPolicy;
import org.tripsphere.common.v1.Address;
import org.tripsphere.common.v1.GeoPoint;
import org.tripsphere.poi.domain.model.GeoCoordinate;
import org.tripsphere.poi.domain.model.Poi;
import org.tripsphere.poi.domain.model.PoiAddress;

@Mapper(
        componentModel = MappingConstants.ComponentModel.SPRING,
        collectionMappingStrategy = CollectionMappingStrategy.ADDER_PREFERRED,
        nullValueCheckStrategy = NullValueCheckStrategy.ALWAYS,
        unmappedSourcePolicy = ReportingPolicy.IGNORE,
        unmappedTargetPolicy = ReportingPolicy.IGNORE)
public interface PoiProtoMapper {

    // Domain → Proto

    org.tripsphere.poi.v1.Poi toProto(Poi poi);

    List<org.tripsphere.poi.v1.Poi> toProtos(List<Poi> pois);

    Address toProtoAddress(PoiAddress address);

    // Proto → Domain

    PoiAddress fromProtoAddress(Address address);

    // GeoCoordinate (WGS84) → GeoPoint proto (GCJ-02)
    default GeoPoint toGeoPoint(GeoCoordinate coord) {
        if (coord == null) return null;
        double[] gcj02 = coord.toGcj02();
        return GeoPoint.newBuilder()
                .setLongitude(gcj02[0])
                .setLatitude(gcj02[1])
                .build();
    }

    // GeoPoint proto (GCJ-02) → GeoCoordinate (WGS84)
    default GeoCoordinate fromGeoPoint(GeoPoint point) {
        if (point == null) return null;
        return GeoCoordinate.fromGcj02(point.getLongitude(), point.getLatitude());
    }
}
