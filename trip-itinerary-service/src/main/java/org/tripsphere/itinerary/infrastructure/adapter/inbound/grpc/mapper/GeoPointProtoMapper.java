package org.tripsphere.itinerary.infrastructure.adapter.inbound.grpc.mapper;

import org.mapstruct.Mapper;
import org.mapstruct.NullValueCheckStrategy;
import org.mapstruct.ReportingPolicy;
import org.tripsphere.itinerary.domain.model.GeoPoint;

@Mapper(
        componentModel = "spring",
        unmappedTargetPolicy = ReportingPolicy.IGNORE,
        nullValueCheckStrategy = NullValueCheckStrategy.ALWAYS)
public interface GeoPointProtoMapper {

    GeoPoint toDomain(org.tripsphere.common.v1.GeoPoint geoPoint);

    org.tripsphere.common.v1.GeoPoint toProto(GeoPoint domain);
}
