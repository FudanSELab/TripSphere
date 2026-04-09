package org.tripsphere.itinerary.application.service.command;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.tripsphere.itinerary.application.dto.AddActivityCommand;
import org.tripsphere.itinerary.application.exception.NotFoundException;
import org.tripsphere.itinerary.application.port.ItineraryRepository;
import org.tripsphere.itinerary.domain.model.Activity;
import org.tripsphere.itinerary.domain.model.Itinerary;

@Slf4j
@Service
@RequiredArgsConstructor
public class AddActivityUseCase {

    private final ItineraryRepository itineraryRepository;

    public Activity execute(AddActivityCommand command) {
        log.debug(
                "Adding activity to day plan {} in itinerary {} at index {}",
                command.dayPlanId(),
                command.itineraryId(),
                command.insertIndex());

        Itinerary itinerary = itineraryRepository
                .findById(command.itineraryId())
                .orElseThrow(() -> new NotFoundException("Itinerary", command.itineraryId()));

        Activity added = itinerary.addActivity(command.dayPlanId(), command.activity(), command.insertIndex());

        itineraryRepository.save(itinerary);
        log.info(
                "Added activity {} to day plan {} in itinerary {}",
                added.getId(),
                command.dayPlanId(),
                command.itineraryId());
        return added;
    }
}
