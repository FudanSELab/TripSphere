package org.tripsphere.poi.application.port;

import java.util.List;
import java.util.Optional;
import org.tripsphere.poi.domain.model.GeoCoordinate;
import org.tripsphere.poi.domain.model.Poi;

public interface PoiRepository {

    Optional<Poi> findById(String id);

    List<Poi> findByIds(List<String> ids);

    /**
     * Find POIs within a given radius of a center point.
     *
     * @param center center point in WGS84
     * @param radiusMeters search radius in meters
     * @param limit maximum number of results
     * @param categories optional category filter (null or empty means no filter)
     * @param adcode optional administrative area code filter (null or empty means no filter)
     */
    List<Poi> findNearby(GeoCoordinate center, double radiusMeters, int limit, List<String> categories, String adcode);

    /**
     * Find POIs within a bounding box.
     *
     * @param southWest south-west corner in WGS84
     * @param northEast north-east corner in WGS84
     * @param limit maximum number of results
     * @param categories optional category filter (null or empty means no filter)
     * @param adcode optional administrative area code filter (null or empty means no filter)
     */
    List<Poi> findInBounds(
            GeoCoordinate southWest, GeoCoordinate northEast, int limit, List<String> categories, String adcode);

    Poi save(Poi poi);

    List<Poi> saveAll(List<Poi> pois);
}
