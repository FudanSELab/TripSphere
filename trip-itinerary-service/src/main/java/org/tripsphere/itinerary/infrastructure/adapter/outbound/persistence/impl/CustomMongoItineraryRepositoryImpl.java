package org.tripsphere.itinerary.infrastructure.adapter.outbound.persistence.impl;

import java.time.Instant;
import java.util.List;
import java.util.Optional;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Sort;
import org.springframework.data.mongodb.core.MongoTemplate;
import org.springframework.data.mongodb.core.query.Criteria;
import org.springframework.data.mongodb.core.query.Query;
import org.springframework.stereotype.Repository;
import org.tripsphere.itinerary.infrastructure.adapter.outbound.persistence.CustomMongoItineraryRepository;
import org.tripsphere.itinerary.infrastructure.adapter.outbound.persistence.document.ItineraryDocument;

@Repository
@RequiredArgsConstructor
public class CustomMongoItineraryRepositoryImpl implements CustomMongoItineraryRepository {

    private final MongoTemplate mongoTemplate;

    @Override
    public List<ItineraryDocument> findByUserIdWithPagination(
            String userId, int limit, Instant cursorCreatedAt, String cursorId) {
        Criteria criteria = Criteria.where("userId").is(userId);

        if (cursorCreatedAt != null && cursorId != null) {
            criteria.orOperator(
                    Criteria.where("createdAt").lt(cursorCreatedAt),
                    Criteria.where("createdAt").is(cursorCreatedAt).and("_id").lt(cursorId));
        }

        Query query = new Query(criteria)
                .with(Sort.by(Sort.Direction.DESC, "createdAt").and(Sort.by(Sort.Direction.DESC, "_id")))
                .limit(limit);

        return mongoTemplate.find(query, ItineraryDocument.class);
    }

    @Override
    public Optional<ItineraryDocument> findByActivityId(String activityId) {
        Query query = new Query(Criteria.where("dayPlans.activities.id").is(activityId));
        return Optional.ofNullable(mongoTemplate.findOne(query, ItineraryDocument.class));
    }
}
