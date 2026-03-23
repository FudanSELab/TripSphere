package org.tripsphere.attraction.repository.impl;

import java.util.List;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.geo.Point;
import org.springframework.data.mongodb.core.MongoTemplate;
import org.springframework.data.mongodb.core.query.Criteria;
import org.springframework.data.mongodb.core.query.Query;
import org.springframework.stereotype.Repository;
import org.tripsphere.attraction.model.AttractionDoc;
import org.tripsphere.attraction.repository.CustomAttractionDocRepository;

@Repository
@RequiredArgsConstructor
public class CustomAttractionDocRepositoryImpl implements CustomAttractionDocRepository {

    private final MongoTemplate mongoTemplate;

    @Override
    public List<AttractionDoc> findAllByLocationNear(
            Point location, double radiusMeters, int limit, List<String> tags) {
        Criteria criteria = Criteria.where("location").nearSphere(location).maxDistance(radiusMeters);

        if (tags != null && !tags.isEmpty()) {
            criteria.and("tags").in(tags);
        }

        Query query = new Query(criteria).with(PageRequest.of(0, limit));

        return mongoTemplate.find(query, AttractionDoc.class);
    }
}
