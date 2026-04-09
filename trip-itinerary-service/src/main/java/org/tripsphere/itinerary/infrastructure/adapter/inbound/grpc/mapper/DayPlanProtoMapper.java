package org.tripsphere.itinerary.infrastructure.adapter.inbound.grpc.mapper;

import java.util.List;
import org.mapstruct.CollectionMappingStrategy;
import org.mapstruct.Mapper;
import org.mapstruct.NullValueCheckStrategy;
import org.mapstruct.ReportingPolicy;
import org.tripsphere.itinerary.domain.model.DayPlan;

@Mapper(
        componentModel = "spring",
        collectionMappingStrategy = CollectionMappingStrategy.ADDER_PREFERRED,
        unmappedTargetPolicy = ReportingPolicy.IGNORE,
        nullValueCheckStrategy = NullValueCheckStrategy.ALWAYS,
        uses = {CommonProtoMapper.class, ActivityProtoMapper.class})
public interface DayPlanProtoMapper {

    DayPlan toDomain(org.tripsphere.itinerary.v1.DayPlan proto);

    org.tripsphere.itinerary.v1.DayPlan toProto(DayPlan domain);

    List<DayPlan> toDomainList(List<org.tripsphere.itinerary.v1.DayPlan> protos);

    List<org.tripsphere.itinerary.v1.DayPlan> toProtoList(List<DayPlan> domains);
}
