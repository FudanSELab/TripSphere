package org.tripsphere.attraction.infrastructure.adapter.inbound.grpc.mapper;

import java.util.List;
import org.mapstruct.CollectionMappingStrategy;
import org.mapstruct.Mapper;
import org.mapstruct.Mapping;
import org.mapstruct.NullValueCheckStrategy;
import org.mapstruct.ReportingPolicy;
import org.tripsphere.attraction.domain.model.Attraction;
import org.tripsphere.attraction.domain.model.OpenRule;

@Mapper(
        componentModel = "spring",
        collectionMappingStrategy = CollectionMappingStrategy.ADDER_PREFERRED,
        unmappedTargetPolicy = ReportingPolicy.IGNORE,
        nullValueCheckStrategy = NullValueCheckStrategy.ALWAYS,
        uses = {CommonProtoMapper.class})
public interface AttractionProtoMapper {

    @Mapping(target = "location", source = "location", qualifiedByName = "toGeoPointGCJ02")
    org.tripsphere.attraction.v1.Attraction toProto(Attraction domain);

    List<org.tripsphere.attraction.v1.Attraction> toProtoList(List<Attraction> domains);

    @Mapping(target = "location", source = "location", qualifiedByName = "toGeoLocationWGS84")
    Attraction toDomain(org.tripsphere.attraction.v1.Attraction proto);

    org.tripsphere.attraction.v1.OpeningHours toProto(org.tripsphere.attraction.domain.model.OpeningHours openingHours);

    org.tripsphere.attraction.domain.model.OpeningHours toDomain(org.tripsphere.attraction.v1.OpeningHours proto);

    org.tripsphere.attraction.v1.OpenRule toProto(org.tripsphere.attraction.domain.model.OpenRule openRule);

    org.tripsphere.attraction.domain.model.OpenRule toDomain(org.tripsphere.attraction.v1.OpenRule proto);

    org.tripsphere.attraction.v1.TimeRange toProto(OpenRule.TimeRange timeRange);

    OpenRule.TimeRange toDomain(org.tripsphere.attraction.v1.TimeRange proto);

    org.tripsphere.attraction.v1.TicketInfo toProto(org.tripsphere.attraction.domain.model.TicketInfo ticketInfo);

    org.tripsphere.attraction.domain.model.TicketInfo toDomain(org.tripsphere.attraction.v1.TicketInfo proto);

    org.tripsphere.attraction.v1.RecommendTime toProto(
            org.tripsphere.attraction.domain.model.RecommendTime recommendTime);

    org.tripsphere.attraction.domain.model.RecommendTime toDomain(org.tripsphere.attraction.v1.RecommendTime proto);

    org.tripsphere.common.v1.Address toProtoAddress(org.tripsphere.attraction.domain.model.Address address);

    org.tripsphere.attraction.domain.model.Address toDomainAddress(org.tripsphere.common.v1.Address proto);
}
