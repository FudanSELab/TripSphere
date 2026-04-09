package org.tripsphere.attraction.application.port;

import java.util.List;
import java.util.Optional;
import org.tripsphere.attraction.domain.model.Attraction;
import org.tripsphere.attraction.domain.model.GeoLocation;

public interface AttractionRepository {

    Optional<Attraction> findById(String id);

    List<Attraction> findAllByIds(List<String> ids);

    Optional<Attraction> findByPoiId(String poiId);

    List<Attraction> findAllByLocationNear(
            GeoLocation wgs84Location, double radiusMeters, int limit, List<String> tags);

    List<Attraction> listByCity(String city, List<String> tags, int pageSize, int skip);
}
