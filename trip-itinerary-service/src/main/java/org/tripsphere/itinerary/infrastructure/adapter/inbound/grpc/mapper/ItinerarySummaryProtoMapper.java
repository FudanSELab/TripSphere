package org.tripsphere.itinerary.infrastructure.adapter.inbound.grpc.mapper;

import org.mapstruct.CollectionMappingStrategy;
import org.mapstruct.Mapper;
import org.mapstruct.NullValueCheckStrategy;
import org.mapstruct.ReportingPolicy;
import org.tripsphere.itinerary.domain.model.ItinerarySummary;

@Mapper(
        componentModel = "spring",
        collectionMappingStrategy = CollectionMappingStrategy.ADDER_PREFERRED,
        unmappedTargetPolicy = ReportingPolicy.IGNORE,
        nullValueCheckStrategy = NullValueCheckStrategy.ALWAYS,
        uses = MoneyProtoMapper.class)
public interface ItinerarySummaryProtoMapper {

    ItinerarySummary toDomain(org.tripsphere.itinerary.v1.ItinerarySummary proto);

    org.tripsphere.itinerary.v1.ItinerarySummary toProto(ItinerarySummary domain);
}
