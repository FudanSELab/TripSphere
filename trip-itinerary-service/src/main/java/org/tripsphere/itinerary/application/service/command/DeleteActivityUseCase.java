package org.tripsphere.itinerary.application.service.command;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.tripsphere.itinerary.application.exception.NotFoundException;
import org.tripsphere.itinerary.application.port.ItineraryRepository;
import org.tripsphere.itinerary.domain.model.Itinerary;

@Slf4j
@Service
@RequiredArgsConstructor
public class DeleteActivityUseCase {

    private final ItineraryRepository itineraryRepository;

    public void execute(String itineraryId, String dayPlanId, String activityId) {
        log.debug("Deleting activity {} from day plan {} in itinerary {}", activityId, dayPlanId, itineraryId);

        Itinerary itinerary = itineraryRepository
                .findById(itineraryId)
                .orElseThrow(() -> new NotFoundException("Itinerary", itineraryId));

        itinerary.removeActivity(dayPlanId, activityId);

        itineraryRepository.save(itinerary);
        log.info("Deleted activity {} from day plan {} in itinerary {}", activityId, dayPlanId, itineraryId);
    }
}
