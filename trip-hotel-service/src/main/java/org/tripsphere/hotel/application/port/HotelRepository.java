package org.tripsphere.hotel.application.port;

import java.time.Instant;
import java.util.List;
import java.util.Optional;
import org.tripsphere.hotel.domain.model.GeoLocation;
import org.tripsphere.hotel.domain.model.Hotel;

public interface HotelRepository {

    Optional<Hotel> findById(String id);

    List<Hotel> findAllByIds(List<String> ids);

    List<Hotel> findAllByLocationNear(GeoLocation wgs84Location, double radiusMeters, int limit);

    List<Hotel> findByAddressWithPagination(
            String province, String city, int limit, Instant cursorCreatedAt, String cursorId);
}
