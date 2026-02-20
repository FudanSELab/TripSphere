package org.tripsphere.itinerary.repository;

import java.time.Instant;
import java.util.List;
import java.util.Optional;
import org.springframework.data.domain.Pageable;
import org.springframework.data.mongodb.repository.MongoRepository;
import org.springframework.data.mongodb.repository.Query;
import org.tripsphere.itinerary.model.ItineraryDoc;

/** MongoDB repository for itinerary documents. */
public interface ItineraryRepository extends MongoRepository<ItineraryDoc, String> {

    @Query(
            value =
                    """
                    {
                      'userId': ?0,
                      '$or': [
                        { 'createdAt': { '$lt': ?1 } },
                        { 'createdAt': ?1, '_id': { '$lt': ?2 } }
                      ]
                    }
                    """,
            sort = "{ 'createdAt': -1, '_id': -1 }")
    List<ItineraryDoc> findByUserIdWithCursor(
            String userId, Instant cursorCreatedAt, String cursorId, Pageable pageable);

    List<ItineraryDoc> findByUserIdOrderByCreatedAtDescIdDesc(String userId, Pageable pageable);

    @Query("{ 'dayPlans.activities.id': ?0 }")
    Optional<ItineraryDoc> findByActivityId(String activityId);
}
