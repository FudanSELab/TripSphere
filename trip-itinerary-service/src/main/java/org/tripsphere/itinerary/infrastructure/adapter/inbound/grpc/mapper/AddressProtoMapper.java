package org.tripsphere.itinerary.infrastructure.adapter.inbound.grpc.mapper;

import org.mapstruct.Mapper;
import org.mapstruct.NullValueCheckStrategy;
import org.mapstruct.ReportingPolicy;
import org.tripsphere.itinerary.domain.model.Address;

@Mapper(
        componentModel = "spring",
        unmappedTargetPolicy = ReportingPolicy.IGNORE,
        nullValueCheckStrategy = NullValueCheckStrategy.ALWAYS)
public interface AddressProtoMapper {

    Address toDomain(org.tripsphere.common.v1.Address address);

    org.tripsphere.common.v1.Address toProto(Address domain);
}
