package org.tripsphere.itinerary.application.service.query;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.tripsphere.itinerary.application.exception.NotFoundException;
import org.tripsphere.itinerary.application.port.ItineraryRepository;
import org.tripsphere.itinerary.domain.model.Itinerary;

@Slf4j
@Service
@RequiredArgsConstructor
public class GetItineraryUseCase {

    private final ItineraryRepository itineraryRepository;

    public Itinerary execute(String id) {
        log.debug("Getting itinerary by id: {}", id);
        return itineraryRepository.findById(id).orElseThrow(() -> new NotFoundException("Itinerary", id));
    }
}
