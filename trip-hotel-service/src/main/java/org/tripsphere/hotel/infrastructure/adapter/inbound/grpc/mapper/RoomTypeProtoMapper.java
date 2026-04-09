package org.tripsphere.hotel.infrastructure.adapter.inbound.grpc.mapper;

import java.util.List;
import org.mapstruct.CollectionMappingStrategy;
import org.mapstruct.Mapper;
import org.mapstruct.NullValueCheckStrategy;
import org.mapstruct.ReportingPolicy;
import org.tripsphere.hotel.domain.model.RoomType;

@Mapper(
        componentModel = "spring",
        collectionMappingStrategy = CollectionMappingStrategy.ADDER_PREFERRED,
        unmappedTargetPolicy = ReportingPolicy.IGNORE,
        nullValueCheckStrategy = NullValueCheckStrategy.ALWAYS)
public interface RoomTypeProtoMapper {

    org.tripsphere.hotel.v1.RoomType toProto(RoomType domain);

    List<org.tripsphere.hotel.v1.RoomType> toProtoList(List<RoomType> domains);

    RoomType toDomain(org.tripsphere.hotel.v1.RoomType proto);
}
