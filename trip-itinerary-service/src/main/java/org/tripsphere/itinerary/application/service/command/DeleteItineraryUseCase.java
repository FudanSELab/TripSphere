package org.tripsphere.itinerary.application.service.command;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.tripsphere.itinerary.application.exception.NotFoundException;
import org.tripsphere.itinerary.application.port.ItineraryRepository;

@Slf4j
@Service
@RequiredArgsConstructor
public class DeleteItineraryUseCase {

    private final ItineraryRepository itineraryRepository;

    public void execute(String id) {
        log.debug("Deleting itinerary: {}", id);

        if (!itineraryRepository.existsById(id)) {
            throw new NotFoundException("Itinerary", id);
        }

        itineraryRepository.deleteById(id);
        log.info("Deleted itinerary with id: {}", id);
    }
}
