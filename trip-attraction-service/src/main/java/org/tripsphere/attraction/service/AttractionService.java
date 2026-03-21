package org.tripsphere.attraction.service;

import java.util.List;
import java.util.Optional;
import org.tripsphere.attraction.v1.Attraction;
import org.tripsphere.common.v1.GeoPoint;

public interface AttractionService {

    /**
     * Find an attraction by its ID.
     *
     * @param id the attraction ID
     * @return the attraction if found
     */
    Optional<Attraction> findById(String id);

    /**
     * Find all attractions by their IDs.
     *
     * @param ids the list of attraction IDs
     * @return list of attractions found
     */
    List<Attraction> findAllByIds(List<String> ids);

    /**
     * Search for attractions near a given location.
     *
     * @param location the center point in GCJ-02 coordinate system
     * @param radiusMeters the search radius in meters
     * @param tags optional filter by tags (can be null or empty)
     * @return list of nearby attractions ordered from near to far
     */
    List<Attraction> searchNearby(GeoPoint location, double radiusMeters, List<String> tags);

    /**
     * Find an attraction by its POI ID.
     *
     * @param poiId the POI ID
     * @return the attraction if found
     */
    Optional<Attraction> findByPoiId(String poiId);

    /**
     * List attractions in a given city with optional tag filter and skip-based pagination.
     *
     * @param city the city name (e.g. "上海市")
     * @param tags optional tag filter; null or empty means no filter
     * @param pageSize number of results to return
     * @param skip number of results to skip
     * @return list of attractions in the city
     */
    List<Attraction> listByCity(String city, List<String> tags, int pageSize, int skip);
}
