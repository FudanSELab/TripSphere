package org.tripsphere.hotel.infrastructure.adapter.inbound.grpc.mapper;

import java.util.List;
import org.mapstruct.CollectionMappingStrategy;
import org.mapstruct.Mapper;
import org.mapstruct.Mapping;
import org.mapstruct.NullValueCheckStrategy;
import org.mapstruct.ReportingPolicy;
import org.tripsphere.hotel.domain.model.BreakfastPolicy;
import org.tripsphere.hotel.domain.model.Hotel;
import org.tripsphere.hotel.domain.model.HotelInformation;
import org.tripsphere.hotel.domain.model.HotelPolicy;

@Mapper(
        componentModel = "spring",
        collectionMappingStrategy = CollectionMappingStrategy.ADDER_PREFERRED,
        unmappedTargetPolicy = ReportingPolicy.IGNORE,
        nullValueCheckStrategy = NullValueCheckStrategy.ALWAYS,
        uses = {CommonProtoMapper.class})
public interface HotelProtoMapper {

    @Mapping(target = "location", source = "location", qualifiedByName = "toGeoPointGCJ02")
    org.tripsphere.hotel.v1.Hotel toProto(Hotel domain);

    List<org.tripsphere.hotel.v1.Hotel> toProtoList(List<Hotel> domains);

    @Mapping(target = "location", source = "location", qualifiedByName = "toGeoLocationWGS84")
    Hotel toDomain(org.tripsphere.hotel.v1.Hotel proto);

    org.tripsphere.hotel.v1.HotelInformation toProto(HotelInformation information);

    HotelInformation toDomain(org.tripsphere.hotel.v1.HotelInformation proto);

    org.tripsphere.hotel.v1.HotelPolicy toProto(HotelPolicy policy);

    HotelPolicy toDomain(org.tripsphere.hotel.v1.HotelPolicy proto);

    org.tripsphere.hotel.v1.BreakfastPolicy toProto(BreakfastPolicy breakfast);

    BreakfastPolicy toDomain(org.tripsphere.hotel.v1.BreakfastPolicy proto);

    org.tripsphere.common.v1.Address toProtoAddress(org.tripsphere.hotel.domain.model.Address address);

    org.tripsphere.hotel.domain.model.Address toDomainAddress(org.tripsphere.common.v1.Address proto);
}
