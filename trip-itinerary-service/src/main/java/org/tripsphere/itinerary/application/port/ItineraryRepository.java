package org.tripsphere.itinerary.application.port;

import java.time.Instant;
import java.util.List;
import java.util.Optional;
import org.tripsphere.itinerary.domain.model.Itinerary;

public interface ItineraryRepository {

    Itinerary save(Itinerary itinerary);

    Optional<Itinerary> findById(String id);

    Optional<Itinerary> findByActivityId(String activityId);

    List<Itinerary> findByUserIdWithPagination(String userId, int limit, Instant cursorCreatedAt, String cursorId);

    boolean existsById(String id);

    void deleteById(String id);
}
