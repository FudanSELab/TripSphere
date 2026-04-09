package org.tripsphere.itinerary.infrastructure.adapter.inbound.grpc.mapper;

import java.util.List;
import org.mapstruct.AfterMapping;
import org.mapstruct.CollectionMappingStrategy;
import org.mapstruct.Mapper;
import org.mapstruct.Mapping;
import org.mapstruct.MappingTarget;
import org.mapstruct.NullValueCheckStrategy;
import org.mapstruct.ReportingPolicy;
import org.tripsphere.common.v1.Address;
import org.tripsphere.itinerary.domain.model.Activity;
import org.tripsphere.itinerary.domain.model.ActivityKind;

@Mapper(
        componentModel = "spring",
        collectionMappingStrategy = CollectionMappingStrategy.ADDER_PREFERRED,
        unmappedTargetPolicy = ReportingPolicy.IGNORE,
        nullValueCheckStrategy = NullValueCheckStrategy.ALWAYS,
        uses = {CommonProtoMapper.class, MoneyProtoMapper.class, GeoPointProtoMapper.class, AddressProtoMapper.class})
public interface ActivityProtoMapper {

    @Mapping(target = "attractionId", source = "attraction.id")
    @Mapping(target = "hotelId", source = "hotel.id")
    @Mapping(target = "location.name", ignore = true)
    @Mapping(target = "location.lineAddress", ignore = true)
    Activity toDomain(org.tripsphere.itinerary.v1.Activity proto);

    @Mapping(target = "attraction", ignore = true)
    @Mapping(target = "hotel", ignore = true)
    org.tripsphere.itinerary.v1.Activity toProto(Activity domain);

    @AfterMapping
    default void mergeLegacyFlatAddressIntoProto(
            Activity domain, @MappingTarget org.tripsphere.itinerary.v1.Activity.Builder builder) {
        if (domain == null || domain.getLocation() == null) return;
        String line = domain.getLocation().lineAddress();
        if (line == null || line.isBlank()) return;
        Address built = builder.getAddress();
        if (built != null && !built.getDetailed().isBlank()) return;
        builder.setAddress(Address.newBuilder().setDetailed(line).build());
    }

    List<Activity> toDomainList(List<org.tripsphere.itinerary.v1.Activity> protos);

    List<org.tripsphere.itinerary.v1.Activity> toProtoList(List<Activity> domains);

    default ActivityKind toActivityKind(org.tripsphere.itinerary.v1.ActivityKind protoKind) {
        if (protoKind == null) return ActivityKind.UNSPECIFIED;
        return switch (protoKind) {
            case ACTIVITY_KIND_ATTRACTION_VISIT -> ActivityKind.ATTRACTION_VISIT;
            case ACTIVITY_KIND_DINING -> ActivityKind.DINING;
            case ACTIVITY_KIND_HOTEL_STAY -> ActivityKind.HOTEL_STAY;
            case ACTIVITY_KIND_CUSTOM -> ActivityKind.CUSTOM;
            default -> ActivityKind.UNSPECIFIED;
        };
    }

    default org.tripsphere.itinerary.v1.ActivityKind toActivityKindProto(ActivityKind kind) {
        if (kind == null) return org.tripsphere.itinerary.v1.ActivityKind.ACTIVITY_KIND_UNSPECIFIED;
        return switch (kind) {
            case ATTRACTION_VISIT -> org.tripsphere.itinerary.v1.ActivityKind.ACTIVITY_KIND_ATTRACTION_VISIT;
            case DINING -> org.tripsphere.itinerary.v1.ActivityKind.ACTIVITY_KIND_DINING;
            case HOTEL_STAY -> org.tripsphere.itinerary.v1.ActivityKind.ACTIVITY_KIND_HOTEL_STAY;
            case CUSTOM -> org.tripsphere.itinerary.v1.ActivityKind.ACTIVITY_KIND_CUSTOM;
            default -> org.tripsphere.itinerary.v1.ActivityKind.ACTIVITY_KIND_UNSPECIFIED;
        };
    }
}
