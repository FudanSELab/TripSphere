package org.tripsphere.attraction.application.service.query;

import java.util.List;
import java.util.Map;
import java.util.function.Function;
import java.util.stream.Collectors;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.tripsphere.attraction.application.exception.NotFoundException;
import org.tripsphere.attraction.application.port.AttractionRepository;
import org.tripsphere.attraction.domain.model.Attraction;

@Service
@RequiredArgsConstructor
public class BatchGetAttractionsUseCase {

    private final AttractionRepository attractionRepository;

    public List<Attraction> execute(List<String> ids) {
        List<Attraction> attractions = attractionRepository.findAllByIds(ids);

        Map<String, Attraction> byId =
                attractions.stream().collect(Collectors.toMap(Attraction::getId, Function.identity()));

        List<String> missingIds =
                ids.stream().filter(id -> !byId.containsKey(id)).toList();
        if (!missingIds.isEmpty()) {
            throw new NotFoundException("Attractions with IDs " + missingIds + " not found");
        }

        return ids.stream().map(byId::get).toList();
    }
}
