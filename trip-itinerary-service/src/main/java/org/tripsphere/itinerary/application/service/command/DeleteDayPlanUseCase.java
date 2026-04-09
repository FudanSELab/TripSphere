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
public class DeleteDayPlanUseCase {

    private final ItineraryRepository itineraryRepository;

    public void execute(String itineraryId, String dayPlanId) {
        log.debug("Deleting day plan {} from itinerary {}", dayPlanId, itineraryId);

        Itinerary itinerary = itineraryRepository
                .findById(itineraryId)
                .orElseThrow(() -> new NotFoundException("Itinerary", itineraryId));

        itinerary.removeDayPlan(dayPlanId);

        itineraryRepository.save(itinerary);
        log.info("Deleted day plan {} from itinerary {}", dayPlanId, itineraryId);
    }
}
