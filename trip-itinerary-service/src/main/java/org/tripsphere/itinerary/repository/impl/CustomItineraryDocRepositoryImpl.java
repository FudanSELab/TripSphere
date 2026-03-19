package org.tripsphere.itinerary.repository.impl;

import java.time.Instant;
import java.util.List;
import java.util.Optional;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Sort;
import org.springframework.data.mongodb.core.MongoTemplate;
import org.springframework.data.mongodb.core.query.Criteria;
import org.springframework.data.mongodb.core.query.Query;
import org.springframework.stereotype.Repository;
import org.tripsphere.itinerary.model.ItineraryDoc;
import org.tripsphere.itinerary.repository.CustomItineraryDocRepository;

@Repository
@RequiredArgsConstructor
public class CustomItineraryDocRepositoryImpl implements CustomItineraryDocRepository {

    private final MongoTemplate mongoTemplate;

    @Override
    public List<ItineraryDoc> findByUserIdWithPagination(
            String userId, int limit, Instant cursorCreatedAt, String cursorId) {
        Criteria criteria = Criteria.where("userId").is(userId);

        // Keyset pagination: skip past the cursor using (createdAt DESC, _id DESC)
        if (cursorCreatedAt != null && cursorId != null) {
            criteria.orOperator(
                    Criteria.where("createdAt").lt(cursorCreatedAt),
                    Criteria.where("createdAt").is(cursorCreatedAt).and("_id").lt(cursorId));
        }

        Query query = new Query(criteria)
                .with(Sort.by(Sort.Direction.DESC, "createdAt").and(Sort.by(Sort.Direction.DESC, "_id")))
                .limit(limit);

        return mongoTemplate.find(query, ItineraryDoc.class);
    }

    @Override
    public Optional<ItineraryDoc> findByActivityId(String activityId) {
        Query query = new Query(Criteria.where("dayPlans.activities.id").is(activityId));
        return Optional.ofNullable(mongoTemplate.findOne(query, ItineraryDoc.class));
    }
}
