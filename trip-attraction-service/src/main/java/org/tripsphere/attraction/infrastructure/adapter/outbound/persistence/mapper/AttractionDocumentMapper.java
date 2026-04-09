package org.tripsphere.attraction.infrastructure.adapter.outbound.persistence.mapper;

import java.util.List;
import org.mapstruct.CollectionMappingStrategy;
import org.mapstruct.Mapper;
import org.mapstruct.NullValueCheckStrategy;
import org.mapstruct.ReportingPolicy;
import org.springframework.data.mongodb.core.geo.GeoJsonPoint;
import org.tripsphere.attraction.domain.model.Attraction;
import org.tripsphere.attraction.domain.model.GeoLocation;
import org.tripsphere.attraction.infrastructure.adapter.outbound.persistence.document.AttractionDocument;

@Mapper(
        componentModel = "spring",
        collectionMappingStrategy = CollectionMappingStrategy.ADDER_PREFERRED,
        unmappedTargetPolicy = ReportingPolicy.IGNORE,
        nullValueCheckStrategy = NullValueCheckStrategy.ALWAYS)
public interface AttractionDocumentMapper {

    Attraction toDomain(AttractionDocument doc);

    List<Attraction> toDomainList(List<AttractionDocument> docs);

    AttractionDocument toDocument(Attraction attraction);

    default GeoLocation toGeoLocation(GeoJsonPoint point) {
        if (point == null) return null;
        return new GeoLocation(point.getX(), point.getY());
    }

    default GeoJsonPoint toGeoJsonPoint(GeoLocation location) {
        if (location == null) return null;
        return new GeoJsonPoint(location.longitude(), location.latitude());
    }
}
