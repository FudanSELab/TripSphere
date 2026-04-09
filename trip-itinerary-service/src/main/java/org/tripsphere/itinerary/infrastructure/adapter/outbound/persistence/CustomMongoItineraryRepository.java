package org.tripsphere.itinerary.infrastructure.adapter.outbound.persistence;

import java.time.Instant;
import java.util.List;
import java.util.Optional;
import org.tripsphere.itinerary.infrastructure.adapter.outbound.persistence.document.ItineraryDocument;

public interface CustomMongoItineraryRepository {

    List<ItineraryDocument> findByUserIdWithPagination(
            String userId, int limit, Instant cursorCreatedAt, String cursorId);

    Optional<ItineraryDocument> findByActivityId(String activityId);
}
