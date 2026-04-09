package org.tripsphere.poi.infrastructure.adapter.outbound.persistence.mapper;

import java.util.List;
import org.mapstruct.Mapper;
import org.mapstruct.MappingConstants;
import org.mapstruct.NullValueCheckStrategy;
import org.mapstruct.ReportingPolicy;
import org.springframework.data.mongodb.core.geo.GeoJsonPoint;
import org.tripsphere.poi.domain.model.GeoCoordinate;
import org.tripsphere.poi.domain.model.Poi;
import org.tripsphere.poi.infrastructure.adapter.outbound.persistence.document.PoiDoc;

@Mapper(
        componentModel = MappingConstants.ComponentModel.SPRING,
        nullValueCheckStrategy = NullValueCheckStrategy.ALWAYS,
        unmappedTargetPolicy = ReportingPolicy.IGNORE)
public interface PoiDocMapper {

    PoiDoc toDoc(Poi poi);

    Poi toDomain(PoiDoc doc);

    List<Poi> toDomains(List<PoiDoc> docs);

    default GeoJsonPoint toGeoJsonPoint(GeoCoordinate coord) {
        if (coord == null) return null;
        return new GeoJsonPoint(coord.longitude(), coord.latitude());
    }

    default GeoCoordinate toGeoCoordinate(GeoJsonPoint point) {
        if (point == null) return null;
        return GeoCoordinate.of(point.getX(), point.getY());
    }
}
