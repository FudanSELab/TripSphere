package org.tripsphere.poi.infrastructure.adapter.outbound.persistence.impl;

import java.util.List;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.geo.Box;
import org.springframework.data.geo.Point;
import org.springframework.data.mongodb.core.MongoTemplate;
import org.springframework.data.mongodb.core.query.Criteria;
import org.springframework.data.mongodb.core.query.Query;
import org.springframework.stereotype.Repository;
import org.tripsphere.poi.infrastructure.adapter.outbound.persistence.CustomPoiDocRepository;
import org.tripsphere.poi.infrastructure.adapter.outbound.persistence.document.PoiDoc;

@Repository
@RequiredArgsConstructor
public class CustomPoiDocRepositoryImpl implements CustomPoiDocRepository {

    private final MongoTemplate mongoTemplate;

    @Override
    public List<PoiDoc> findAllByLocationNear(
            Point location, double radiusMeters, int limit, List<String> categories, String adcode) {
        Criteria criteria = Criteria.where("location").nearSphere(location).maxDistance(radiusMeters);
        applyFilter(criteria, categories, adcode);
        Query query = new Query(criteria).with(PageRequest.of(0, limit));
        return mongoTemplate.find(query, PoiDoc.class);
    }

    @Override
    public List<PoiDoc> findAllByLocationInBox(
            Point southWest, Point northEast, int limit, List<String> categories, String adcode) {
        Criteria criteria = Criteria.where("location").within(new Box(southWest, northEast));
        applyFilter(criteria, categories, adcode);
        Query query = new Query(criteria).with(PageRequest.of(0, limit));
        return mongoTemplate.find(query, PoiDoc.class);
    }

    private void applyFilter(Criteria criteria, List<String> categories, String adcode) {
        if (categories != null && !categories.isEmpty()) {
            criteria.and("categories").in(categories);
        }
        if (adcode != null && !adcode.isEmpty()) {
            criteria.and("adcode").is(adcode);
        }
    }
}
