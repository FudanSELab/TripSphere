package org.tripsphere.attraction.application.service.query;

import java.util.List;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.tripsphere.attraction.application.port.AttractionRepository;
import org.tripsphere.attraction.domain.model.Attraction;
import org.tripsphere.attraction.domain.model.GeoLocation;

@Service
@RequiredArgsConstructor
public class GetAttractionsNearbyUseCase {

    private static final int DEFAULT_NEARBY_LIMIT = 100;

    private final AttractionRepository attractionRepository;

    public List<Attraction> execute(GeoLocation wgs84Location, double radiusMeters, List<String> tags) {
        return attractionRepository.findAllByLocationNear(wgs84Location, radiusMeters, DEFAULT_NEARBY_LIMIT, tags);
    }
}
