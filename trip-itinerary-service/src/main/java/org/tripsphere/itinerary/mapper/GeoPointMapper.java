package org.tripsphere.itinerary.mapper;

import org.mapstruct.CollectionMappingStrategy;
import org.mapstruct.Mapper;
import org.mapstruct.NullValueCheckStrategy;
import org.mapstruct.ReportingPolicy;
import org.mapstruct.factory.Mappers;
import org.tripsphere.common.v1.GeoPoint;
import org.tripsphere.itinerary.model.GeoPointDoc;

@Mapper(
        collectionMappingStrategy = CollectionMappingStrategy.ADDER_PREFERRED,
        unmappedTargetPolicy = ReportingPolicy.IGNORE,
        nullValueCheckStrategy = NullValueCheckStrategy.ALWAYS)
public interface GeoPointMapper {
    GeoPointMapper INSTANCE = Mappers.getMapper(GeoPointMapper.class);

    GeoPointDoc toDoc(GeoPoint geoPoint);

    GeoPoint toProto(GeoPointDoc doc);
}
