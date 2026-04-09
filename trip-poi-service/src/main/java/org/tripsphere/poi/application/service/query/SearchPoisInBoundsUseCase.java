package org.tripsphere.poi.application.service.query;

import java.util.List;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.tripsphere.poi.application.dto.SearchPoisInBoundsQuery;
import org.tripsphere.poi.application.port.PoiRepository;
import org.tripsphere.poi.domain.model.Poi;

@Slf4j
@Service
@RequiredArgsConstructor
public class SearchPoisInBoundsUseCase {

    private final PoiRepository poiRepository;

    public List<Poi> execute(SearchPoisInBoundsQuery query) {
        log.debug(
                "Searching POIs in bounds: SW({}, {}), NE({}, {}), limit: {}",
                query.southWest().longitude(),
                query.southWest().latitude(),
                query.northEast().longitude(),
                query.northEast().latitude(),
                query.limit());
        return poiRepository.findInBounds(
                query.southWest(), query.northEast(), query.limit(), query.categories(), query.adcode());
    }
}
