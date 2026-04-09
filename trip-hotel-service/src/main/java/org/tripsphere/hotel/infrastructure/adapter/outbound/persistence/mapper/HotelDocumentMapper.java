package org.tripsphere.hotel.infrastructure.adapter.outbound.persistence.mapper;

import java.util.List;
import org.mapstruct.CollectionMappingStrategy;
import org.mapstruct.Mapper;
import org.mapstruct.NullValueCheckStrategy;
import org.mapstruct.ReportingPolicy;
import org.springframework.data.mongodb.core.geo.GeoJsonPoint;
import org.tripsphere.hotel.domain.model.GeoLocation;
import org.tripsphere.hotel.domain.model.Hotel;
import org.tripsphere.hotel.infrastructure.adapter.outbound.persistence.document.HotelDocument;

@Mapper(
        componentModel = "spring",
        collectionMappingStrategy = CollectionMappingStrategy.ADDER_PREFERRED,
        unmappedTargetPolicy = ReportingPolicy.IGNORE,
        nullValueCheckStrategy = NullValueCheckStrategy.ALWAYS)
public interface HotelDocumentMapper {

    Hotel toDomain(HotelDocument doc);

    List<Hotel> toDomainList(List<HotelDocument> docs);

    HotelDocument toDocument(Hotel hotel);

    default GeoLocation toGeoLocation(GeoJsonPoint point) {
        if (point == null) return null;
        return new GeoLocation(point.getX(), point.getY());
    }

    default GeoJsonPoint toGeoJsonPoint(GeoLocation location) {
        if (location == null) return null;
        return new GeoJsonPoint(location.longitude(), location.latitude());
    }
}
