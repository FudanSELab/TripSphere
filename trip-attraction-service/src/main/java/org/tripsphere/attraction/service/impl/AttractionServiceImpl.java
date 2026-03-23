package org.tripsphere.attraction.service.impl;

import java.util.List;
import java.util.Optional;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Sort;
import org.springframework.data.geo.Point;
import org.springframework.stereotype.Service;
import org.tripsphere.attraction.mapper.AttractionMapper;
import org.tripsphere.attraction.model.AttractionDoc;
import org.tripsphere.attraction.repository.AttractionDocRepository;
import org.tripsphere.attraction.service.AttractionService;
import org.tripsphere.attraction.util.CoordinateTransformUtil;
import org.tripsphere.attraction.v1.Attraction;
import org.tripsphere.common.v1.GeoPoint;

@Slf4j
@Service
@RequiredArgsConstructor
public class AttractionServiceImpl implements AttractionService {

    private final AttractionDocRepository attractionDocRepository;
    private final AttractionMapper attractionMapper = AttractionMapper.INSTANCE;

    private static final int DEFAULT_NEARBY_LIMIT = 100;

    @Override
    public Optional<Attraction> findById(String id) {
        log.debug("Finding attraction by id: {}", id);
        return attractionDocRepository.findById(id).map(attractionMapper::toProto);
    }

    @Override
    public List<Attraction> findAllByIds(List<String> ids) {
        log.debug("Finding attractions by ids, count: {}", ids.size());
        List<AttractionDoc> docs = attractionDocRepository.findAllById(ids);
        return attractionMapper.toProtoList(docs);
    }

    @Override
    public List<Attraction> searchNearby(GeoPoint location, double radiusMeters, List<String> tags) {
        log.debug(
                "Searching attractions nearby location: ({}, {}), radius: {}m",
                location.getLongitude(),
                location.getLatitude(),
                radiusMeters);

        // Convert GCJ-02 (from client) to WGS84 (for MongoDB)
        Point wgs84Location = toWgs84Point(location);

        List<AttractionDoc> docs =
                attractionDocRepository.findAllByLocationNear(wgs84Location, radiusMeters, DEFAULT_NEARBY_LIMIT, tags);
        return attractionMapper.toProtoList(docs);
    }

    @Override
    public Optional<Attraction> findByPoiId(String poiId) {
        log.debug("Finding attraction by poiId: {}", poiId);
        return attractionDocRepository.findByPoiId(poiId).map(attractionMapper::toProto);
    }

    @Override
    public List<Attraction> listByCity(String city, List<String> tags, int pageSize, int skip) {
        log.debug("Listing attractions by city: {}, tags: {}, pageSize: {}, skip: {}", city, tags, pageSize, skip);
        int effectivePageSize = pageSize > 0 ? pageSize : 12;
        int page = effectivePageSize > 0 ? skip / effectivePageSize : 0;
        PageRequest pageRequest = PageRequest.of(page, effectivePageSize, Sort.by("name"));

        List<AttractionDoc> docs;
        if (tags == null || tags.isEmpty()) {
            docs = attractionDocRepository.findAllByAddressCity(city, pageRequest);
        } else {
            docs = attractionDocRepository.findAllByAddressCityAndTagsIn(city, tags, pageRequest);
        }
        return attractionMapper.toProtoList(docs);
    }

    /** Convert GeoPoint (GCJ-02) to Spring Point (WGS84) for MongoDB queries. */
    private Point toWgs84Point(GeoPoint geoPoint) {
        double[] wgs84 = CoordinateTransformUtil.gcj02ToWgs84(geoPoint.getLongitude(), geoPoint.getLatitude());
        return new Point(wgs84[0], wgs84[1]);
    }
}
