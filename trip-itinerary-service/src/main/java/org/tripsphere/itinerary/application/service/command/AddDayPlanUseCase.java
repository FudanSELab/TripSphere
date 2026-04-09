package org.tripsphere.itinerary.application.service.command;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.tripsphere.itinerary.application.dto.AddDayPlanCommand;
import org.tripsphere.itinerary.application.exception.NotFoundException;
import org.tripsphere.itinerary.application.port.ItineraryRepository;
import org.tripsphere.itinerary.domain.model.DayPlan;
import org.tripsphere.itinerary.domain.model.Itinerary;

@Slf4j
@Service
@RequiredArgsConstructor
public class AddDayPlanUseCase {

    private final ItineraryRepository itineraryRepository;

    public DayPlan execute(AddDayPlanCommand command) {
        log.debug("Adding day plan to itinerary: {}", command.itineraryId());

        Itinerary itinerary = itineraryRepository
                .findById(command.itineraryId())
                .orElseThrow(() -> new NotFoundException("Itinerary", command.itineraryId()));

        DayPlan added = itinerary.addDayPlan(command.dayPlan());

        itineraryRepository.save(itinerary);
        log.info("Added day plan {} to itinerary {}", added.getId(), command.itineraryId());
        return added;
    }
}
