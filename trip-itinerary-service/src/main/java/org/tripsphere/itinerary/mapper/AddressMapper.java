package org.tripsphere.itinerary.mapper;

import org.mapstruct.CollectionMappingStrategy;
import org.mapstruct.Mapper;
import org.mapstruct.NullValueCheckStrategy;
import org.mapstruct.ReportingPolicy;
import org.mapstruct.factory.Mappers;
import org.tripsphere.common.v1.Address;
import org.tripsphere.itinerary.model.AddressDoc;

@Mapper(
        collectionMappingStrategy = CollectionMappingStrategy.ADDER_PREFERRED,
        unmappedTargetPolicy = ReportingPolicy.IGNORE,
        nullValueCheckStrategy = NullValueCheckStrategy.ALWAYS)
public interface AddressMapper {
    AddressMapper INSTANCE = Mappers.getMapper(AddressMapper.class);

    AddressDoc toDoc(Address address);

    Address toProto(AddressDoc doc);
}
