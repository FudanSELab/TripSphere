package org.tripsphere.poi.application.service.query;

import java.util.List;
import java.util.Map;
import java.util.function.Function;
import java.util.stream.Collectors;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.tripsphere.poi.application.exception.InvalidArgumentException;
import org.tripsphere.poi.application.exception.NotFoundException;
import org.tripsphere.poi.application.port.PoiRepository;
import org.tripsphere.poi.domain.model.Poi;

@Slf4j
@Service
@RequiredArgsConstructor
public class BatchFindPoisUseCase {

    private final PoiRepository poiRepository;

    public List<Poi> execute(List<String> ids) {
        if (ids == null) {
            throw InvalidArgumentException.required("ids");
        }
        if (ids.isEmpty()) {
            return List.of();
        }
        log.debug("Finding POIs by ids, count: {}", ids.size());
        List<Poi> pois = poiRepository.findByIds(ids);
        Map<String, Poi> poisById = pois.stream().collect(Collectors.toMap(Poi::getId, Function.identity()));
        List<String> missingIds =
                ids.stream().filter(id -> !poisById.containsKey(id)).toList();
        if (!missingIds.isEmpty()) {
            throw new NotFoundException("POIs with IDs " + missingIds + " not found");
        }
        return ids.stream().map(poisById::get).toList();
    }
}
