package org.tripsphere.attraction.application.service.query;

import java.util.List;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.tripsphere.attraction.application.port.AttractionRepository;
import org.tripsphere.attraction.domain.model.Attraction;
import org.tripsphere.attraction.domain.model.GeoLocation;

@Slf4j
@Service
@RequiredArgsConstructor
public class GetAttractionsNearbyUseCase {

    private static final int DEFAULT_NEARBY_LIMIT = 100;

    private final AttractionRepository attractionRepository;

    public List<Attraction> execute(GeoLocation wgs84Location, double radiusMeters, List<String> tags) {
        List<Attraction> attractions = attractionRepository.findAllByLocationNear(
                wgs84Location, radiusMeters, DEFAULT_NEARBY_LIMIT, tags);
        log.info(
                "Listed nearby attractions: radiusMeters={}, resultCount={}",
                radiusMeters,
                attractions.size());
        return attractions;
    }
}
