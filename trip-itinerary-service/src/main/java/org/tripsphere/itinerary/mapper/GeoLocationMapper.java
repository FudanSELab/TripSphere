package org.tripsphere.itinerary.mapper;

import org.mapstruct.CollectionMappingStrategy;
import org.mapstruct.Mapper;
import org.mapstruct.NullValueCheckStrategy;
import org.mapstruct.ReportingPolicy;
import org.mapstruct.factory.Mappers;
import org.tripsphere.itinerary.model.GeoLocationDoc;
import org.tripsphere.itinerary.v1.GeoLocation;

@Mapper(
        collectionMappingStrategy = CollectionMappingStrategy.ADDER_PREFERRED,
        unmappedTargetPolicy = ReportingPolicy.IGNORE,
        nullValueCheckStrategy = NullValueCheckStrategy.ALWAYS)
public interface GeoLocationMapper {
    GeoLocationMapper INSTANCE = Mappers.getMapper(GeoLocationMapper.class);

    GeoLocationDoc toDoc(GeoLocation geoLocation);

    GeoLocation toProto(GeoLocationDoc doc);
}
