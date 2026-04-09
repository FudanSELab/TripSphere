package org.tripsphere.poi.application.service.query;

import java.util.List;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.tripsphere.poi.application.dto.SearchPoisNearbyQuery;
import org.tripsphere.poi.application.port.PoiRepository;
import org.tripsphere.poi.domain.model.Poi;

@Slf4j
@Service
@RequiredArgsConstructor
public class SearchPoisNearbyUseCase {

    private final PoiRepository poiRepository;

    public List<Poi> execute(SearchPoisNearbyQuery query) {
        log.debug(
                "Searching POIs nearby ({}, {}), radius: {}m, limit: {}",
                query.center().longitude(),
                query.center().latitude(),
                query.radiusMeters(),
                query.limit());
        return poiRepository.findNearby(
                query.center(), query.radiusMeters(), query.limit(), query.categories(), query.adcode());
    }
}
