package org.tripsphere.itinerary.repository;

import java.time.Instant;
import java.util.List;
import java.util.Optional;
import org.tripsphere.itinerary.model.ItineraryDoc;

public interface CustomItineraryDocRepository {

    /**
     * List itineraries for a user with keyset pagination, ordered by createdAt descending.
     *
     * @param userId the user ID to filter by
     * @param limit the maximum number of results to return
     * @param cursorCreatedAt the createdAt value from the last item of the previous page (null for
     *     first page)
     * @param cursorId the id from the last item of the previous page (null for first page)
     * @return list of itineraries
     */
    List<ItineraryDoc> findByUserIdWithPagination(String userId, int limit, Instant cursorCreatedAt, String cursorId);

    /**
     * Find the itinerary that contains a specific activity.
     *
     * @param activityId the activity ID to search for
     * @return the itinerary containing the activity, if found
     */
    Optional<ItineraryDoc> findByActivityId(String activityId);
}
