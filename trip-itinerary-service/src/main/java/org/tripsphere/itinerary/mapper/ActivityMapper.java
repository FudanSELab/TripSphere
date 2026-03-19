package org.tripsphere.itinerary.mapper;

import java.util.List;
import org.mapstruct.AfterMapping;
import org.mapstruct.CollectionMappingStrategy;
import org.mapstruct.Mapper;
import org.mapstruct.Mapping;
import org.mapstruct.MappingTarget;
import org.mapstruct.NullValueCheckStrategy;
import org.mapstruct.ReportingPolicy;
import org.mapstruct.factory.Mappers;
import org.tripsphere.common.v1.Address;
import org.tripsphere.itinerary.model.ActivityDoc;
import org.tripsphere.itinerary.model.ActivityKind;
import org.tripsphere.itinerary.v1.Activity;

@Mapper(
        collectionMappingStrategy = CollectionMappingStrategy.ADDER_PREFERRED,
        unmappedTargetPolicy = ReportingPolicy.IGNORE,
        nullValueCheckStrategy = NullValueCheckStrategy.ALWAYS,
        uses = {CommonMapper.class, MoneyMapper.class, GeoPointMapper.class, AddressMapper.class})
public interface ActivityMapper {
    ActivityMapper INSTANCE = Mappers.getMapper(ActivityMapper.class);

    // ===================================================================
    // Activity Mappings
    // ===================================================================

    @Mapping(target = "attractionId", source = "attraction.id")
    @Mapping(target = "hotelId", source = "hotel.id")
    @Mapping(target = "location.name", ignore = true)
    @Mapping(target = "location.lineAddress", ignore = true)
    ActivityDoc toDoc(Activity activity);

    @Mapping(target = "attraction", ignore = true)
    @Mapping(target = "hotel", ignore = true)
    Activity toProto(ActivityDoc doc);

    /**
     * Legacy Mongo: flat string lived under {@code location.address}. Promote to structured {@link
     * Address} when the new {@code address} object is empty.
     */
    @AfterMapping
    default void mergeLegacyFlatAddressIntoProto(ActivityDoc doc, @MappingTarget Activity.Builder builder) {
        if (doc == null || doc.getLocation() == null) {
            return;
        }
        String line = doc.getLocation().getLineAddress();
        if (line == null || line.isBlank()) {
            return;
        }
        Address built = builder.getAddress();
        if (built != null && !built.getDetailed().isBlank()) {
            return;
        }
        builder.setAddress(Address.newBuilder().setDetailed(line).build());
    }

    List<ActivityDoc> toActivityDocList(List<Activity> activities);

    List<Activity> toActivityProtoList(List<ActivityDoc> docs);

    // ===================================================================
    // ActivityKind Mappings
    // ===================================================================

    default ActivityKind toActivityKind(org.tripsphere.itinerary.v1.ActivityKind protoKind) {
        if (protoKind == null) {
            return ActivityKind.UNSPECIFIED;
        }
        return switch (protoKind) {
            case ACTIVITY_KIND_ATTRACTION_VISIT -> ActivityKind.ATTRACTION_VISIT;
            case ACTIVITY_KIND_DINING -> ActivityKind.DINING;
            case ACTIVITY_KIND_HOTEL_STAY -> ActivityKind.HOTEL_STAY;
            case ACTIVITY_KIND_CUSTOM -> ActivityKind.CUSTOM;
            default -> ActivityKind.UNSPECIFIED;
        };
    }

    default org.tripsphere.itinerary.v1.ActivityKind toActivityKindProto(ActivityKind docKind) {
        if (docKind == null) {
            return org.tripsphere.itinerary.v1.ActivityKind.ACTIVITY_KIND_UNSPECIFIED;
        }
        return switch (docKind) {
            case ATTRACTION_VISIT -> org.tripsphere.itinerary.v1.ActivityKind.ACTIVITY_KIND_ATTRACTION_VISIT;
            case DINING -> org.tripsphere.itinerary.v1.ActivityKind.ACTIVITY_KIND_DINING;
            case HOTEL_STAY -> org.tripsphere.itinerary.v1.ActivityKind.ACTIVITY_KIND_HOTEL_STAY;
            case CUSTOM -> org.tripsphere.itinerary.v1.ActivityKind.ACTIVITY_KIND_CUSTOM;
            default -> org.tripsphere.itinerary.v1.ActivityKind.ACTIVITY_KIND_UNSPECIFIED;
        };
    }
}
