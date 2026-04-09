package org.tripsphere.hotel.application.service.query;

import java.util.List;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.tripsphere.hotel.application.port.HotelRepository;
import org.tripsphere.hotel.domain.model.GeoLocation;
import org.tripsphere.hotel.domain.model.Hotel;

@Service
@RequiredArgsConstructor
public class GetHotelsNearbyUseCase {

    private static final int DEFAULT_NEARBY_LIMIT = 100;

    private final HotelRepository hotelRepository;

    public List<Hotel> execute(GeoLocation wgs84Location, double radiusMeters) {
        return hotelRepository.findAllByLocationNear(wgs84Location, radiusMeters, DEFAULT_NEARBY_LIMIT);
    }
}
