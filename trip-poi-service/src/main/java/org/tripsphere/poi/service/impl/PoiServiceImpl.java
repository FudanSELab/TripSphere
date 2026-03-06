package org.tripsphere.poi.service.impl;

import com.github.f4b6a3.uuid.UuidCreator;
import java.util.List;
import java.util.Optional;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.geo.Point;
import org.springframework.stereotype.Service;
import org.tripsphere.common.v1.GeoPoint;
import org.tripsphere.poi.mapper.PoiMapper;
import org.tripsphere.poi.model.PoiDoc;
import org.tripsphere.poi.model.PoiSearchFilter;
import org.tripsphere.poi.repository.PoiDocRepository;
import org.tripsphere.poi.service.PoiService;
import org.tripsphere.poi.util.CoordinateTransformUtil;
import org.tripsphere.poi.v1.Poi;
import org.tripsphere.poi.v1.PoiFilter;

@Slf4j
@Service
@RequiredArgsConstructor
public class PoiServiceImpl implements PoiService {

    private final PoiDocRepository poiDocRepository;
    private final PoiMapper poiMapper = PoiMapper.INSTANCE;

    @Override
    public Optional<Poi> findById(String id) {
        log.debug("Finding POI by id: {}", id);
        return poiDocRepository.findById(id).map(poiMapper::toProto);
    }

    @Override
    public Optional<Poi> findByAmapId(String amapId) {
        log.debug("Finding POI by amapId: {}", amapId);
        return poiDocRepository.findByAmapId(amapId).map(poiMapper::toProto);
    }

    @Override
    public List<Poi> findAllByIds(List<String> ids) {
        log.debug("Finding POIs by ids, count: {}", ids.size());
        List<PoiDoc> docs = poiDocRepository.findAllById(ids);
        return poiMapper.toProtoList(docs);
    }

    @Override
    public List<Poi> searchNearby(
            GeoPoint location, double radiusMeters, int limit, PoiFilter filter) {
        log.debug(
                "Searching POIs nearby location: ({}, {}), radius: {}m, limit: {}",
                location.getLongitude(),
                location.getLatitude(),
                radiusMeters,
                limit);

        // Convert GCJ-02 (from client) to WGS84 (for MongoDB)
        Point wgs84Location = toWgs84Point(location);
        PoiSearchFilter searchFilter = toSearchFilter(filter);

        List<PoiDoc> docs =
                poiDocRepository.findAllByLocationNear(
                        wgs84Location, radiusMeters, limit, searchFilter);
        return poiMapper.toProtoList(docs);
    }

    @Override
    public List<Poi> searchInBounds(
            GeoPoint southWest, GeoPoint northEast, int limit, PoiFilter filter) {
        log.debug(
                "Searching POIs in bounds: SW({}, {}), NE({}, {}), limit: {}",
                southWest.getLongitude(),
                southWest.getLatitude(),
                northEast.getLongitude(),
                northEast.getLatitude(),
                limit);

        // Convert GCJ-02 (from client) to WGS84 (for MongoDB)
        Point swWgs84 = toWgs84Point(southWest);
        Point neWgs84 = toWgs84Point(northEast);
        PoiSearchFilter searchFilter = toSearchFilter(filter);

        List<PoiDoc> docs =
                poiDocRepository.findAllByLocationInBox(swWgs84, neWgs84, limit, searchFilter);
        return poiMapper.toProtoList(docs);
    }

    @Override
    public Poi createPoi(Poi poi) {
        log.debug("Creating new POI: {}", poi.getName());

        PoiDoc poiDoc = poiMapper.toDoc(poi);
        // Server generates the ID, ignore any client-provided ID
        poiDoc.setId(UuidCreator.getTimeOrderedEpoch().toString());

        PoiDoc saved = poiDocRepository.save(poiDoc);
        log.info("Created POI with id: {}", saved.getId());

        return poiMapper.toProto(saved);
    }

    @Override
    public List<Poi> batchCreatePois(List<Poi> pois) {
        log.debug("Batch creating {} POIs", pois.size());

        // Convert to docs and assign server-generated UUIDs
        List<PoiDoc> toSave =
                pois.stream()
                        .map(poiMapper::toDoc)
                        .peek(doc -> doc.setId(UuidCreator.getTimeOrderedEpoch().toString()))
                        .toList();

        List<PoiDoc> saved = poiDocRepository.saveAll(toSave);
        log.info("Batch created {} POIs", saved.size());

        return poiMapper.toProtoList(saved);
    }

    /** Convert GeoPoint (GCJ-02) to Spring Point (WGS84) for MongoDB queries. */
    private Point toWgs84Point(GeoPoint geoPoint) {
        double[] wgs84 =
                CoordinateTransformUtil.gcj02ToWgs84(
                        geoPoint.getLongitude(), geoPoint.getLatitude());
        return new Point(wgs84[0], wgs84[1]);
    }

    /** Convert Proto PoiFilter to internal PoiSearchFilter. */
    private PoiSearchFilter toSearchFilter(PoiFilter filter) {
        if (filter == null
                || (filter.getCategoriesList().isEmpty() && filter.getAdcode().isEmpty())) {
            return null;
        }
        return PoiSearchFilter.builder()
                .categories(
                        !filter.getCategoriesList().isEmpty() ? filter.getCategoriesList() : null)
                .adcode(!filter.getAdcode().isEmpty() ? filter.getAdcode() : null)
                .build();
    }
}
