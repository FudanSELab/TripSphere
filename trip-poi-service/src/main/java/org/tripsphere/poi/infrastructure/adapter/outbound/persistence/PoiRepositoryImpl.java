package org.tripsphere.poi.infrastructure.adapter.outbound.persistence;

import java.util.List;
import java.util.Optional;
import lombok.RequiredArgsConstructor;
import org.springframework.data.geo.Point;
import org.springframework.stereotype.Repository;
import org.tripsphere.poi.application.port.PoiRepository;
import org.tripsphere.poi.domain.model.GeoCoordinate;
import org.tripsphere.poi.domain.model.Poi;
import org.tripsphere.poi.infrastructure.adapter.outbound.persistence.document.PoiDoc;
import org.tripsphere.poi.infrastructure.adapter.outbound.persistence.mapper.PoiDocMapper;

@Repository
@RequiredArgsConstructor
public class PoiRepositoryImpl implements PoiRepository {

    private final PoiDocRepository poiDocRepository;
    private final PoiDocMapper poiDocMapper;

    @Override
    public Optional<Poi> findById(String id) {
        return poiDocRepository.findById(id).map(poiDocMapper::toDomain);
    }

    @Override
    public List<Poi> findByIds(List<String> ids) {
        return poiDocMapper.toDomains(poiDocRepository.findAllById(ids));
    }

    @Override
    public List<Poi> findNearby(
            GeoCoordinate center, double radiusMeters, int limit, List<String> categories, String adcode) {
        Point point = new Point(center.longitude(), center.latitude());
        List<PoiDoc> docs = poiDocRepository.findAllByLocationNear(point, radiusMeters, limit, categories, adcode);
        return poiDocMapper.toDomains(docs);
    }

    @Override
    public List<Poi> findInBounds(
            GeoCoordinate southWest, GeoCoordinate northEast, int limit, List<String> categories, String adcode) {
        Point sw = new Point(southWest.longitude(), southWest.latitude());
        Point ne = new Point(northEast.longitude(), northEast.latitude());
        List<PoiDoc> docs = poiDocRepository.findAllByLocationInBox(sw, ne, limit, categories, adcode);
        return poiDocMapper.toDomains(docs);
    }

    @Override
    public Poi save(Poi poi) {
        PoiDoc doc = poiDocMapper.toDoc(poi);
        return poiDocMapper.toDomain(poiDocRepository.save(doc));
    }

    @Override
    public List<Poi> saveAll(List<Poi> pois) {
        List<PoiDoc> docs = pois.stream().map(poiDocMapper::toDoc).toList();
        return poiDocMapper.toDomains(poiDocRepository.saveAll(docs));
    }
}
