package org.tripsphere.hotel.repository.impl;

import java.time.Instant;
import java.util.List;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Sort;
import org.springframework.data.geo.Point;
import org.springframework.data.mongodb.core.MongoTemplate;
import org.springframework.data.mongodb.core.query.Criteria;
import org.springframework.data.mongodb.core.query.Query;
import org.springframework.stereotype.Repository;
import org.tripsphere.hotel.model.HotelDoc;
import org.tripsphere.hotel.repository.CustomHotelDocRepository;

@Repository
@RequiredArgsConstructor
public class CustomHotelDocRepositoryImpl implements CustomHotelDocRepository {

    private final MongoTemplate mongoTemplate;

    @Override
    public List<HotelDoc> findAllByLocationNear(Point location, double radiusMeters, int limit) {
        Criteria criteria = Criteria.where("location").nearSphere(location).maxDistance(radiusMeters);

        Query query = new Query(criteria).with(PageRequest.of(0, limit));

        return mongoTemplate.find(query, HotelDoc.class);
    }

    @Override
    public List<HotelDoc> findByAddressWithPagination(
            String province, String city, int limit, Instant cursorCreatedAt, String cursorId) {
        Criteria criteria = new Criteria();

        if (province != null && !province.isEmpty()) {
            criteria.and("address.province").is(province);
        }
        if (city != null && !city.isEmpty()) {
            criteria.and("address.city").is(city);
        }

        // Keyset pagination: skip past the cursor using (createdAt, _id)
        if (cursorCreatedAt != null && cursorId != null) {
            criteria.orOperator(
                    Criteria.where("createdAt").lt(cursorCreatedAt),
                    Criteria.where("createdAt").is(cursorCreatedAt).and("_id").lt(cursorId));
        }

        Query query = new Query(criteria)
                .with(Sort.by(Sort.Direction.DESC, "createdAt").and(Sort.by(Sort.Direction.DESC, "_id")))
                .limit(limit);

        return mongoTemplate.find(query, HotelDoc.class);
    }
}
