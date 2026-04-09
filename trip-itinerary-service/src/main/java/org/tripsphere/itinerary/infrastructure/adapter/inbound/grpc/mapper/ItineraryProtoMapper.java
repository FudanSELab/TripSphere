package org.tripsphere.itinerary.infrastructure.adapter.inbound.grpc.mapper;

import java.util.List;
import org.mapstruct.CollectionMappingStrategy;
import org.mapstruct.Mapper;
import org.mapstruct.Mapping;
import org.mapstruct.NullValueCheckStrategy;
import org.mapstruct.ReportingPolicy;
import org.tripsphere.itinerary.domain.model.Itinerary;

@Mapper(
        componentModel = "spring",
        collectionMappingStrategy = CollectionMappingStrategy.ADDER_PREFERRED,
        unmappedTargetPolicy = ReportingPolicy.IGNORE,
        nullValueCheckStrategy = NullValueCheckStrategy.ALWAYS,
        uses = {
            CommonProtoMapper.class,
            ActivityProtoMapper.class,
            ItinerarySummaryProtoMapper.class,
            DayPlanProtoMapper.class
        })
public interface ItineraryProtoMapper {

    @Mapping(target = "destinationPoiId", source = "destination.id")
    @Mapping(target = "createdAt", ignore = true)
    @Mapping(target = "updatedAt", ignore = true)
    Itinerary toDomain(org.tripsphere.itinerary.v1.Itinerary proto);

    @Mapping(target = "destination", ignore = true)
    @Mapping(target = "createdAt", source = "createdAt")
    @Mapping(target = "updatedAt", source = "updatedAt")
    org.tripsphere.itinerary.v1.Itinerary toProto(Itinerary domain);

    List<org.tripsphere.itinerary.v1.Itinerary> toProtoList(List<Itinerary> domains);
}
