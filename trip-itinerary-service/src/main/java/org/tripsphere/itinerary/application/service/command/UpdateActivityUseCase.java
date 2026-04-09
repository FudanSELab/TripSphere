package org.tripsphere.itinerary.application.service.command;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.tripsphere.itinerary.application.dto.UpdateActivityCommand;
import org.tripsphere.itinerary.application.exception.InvalidArgumentException;
import org.tripsphere.itinerary.application.exception.NotFoundException;
import org.tripsphere.itinerary.application.port.ItineraryRepository;
import org.tripsphere.itinerary.domain.model.Activity;
import org.tripsphere.itinerary.domain.model.Itinerary;

@Slf4j
@Service
@RequiredArgsConstructor
public class UpdateActivityUseCase {

    private final ItineraryRepository itineraryRepository;

    public Activity execute(UpdateActivityCommand command) {
        Activity activity = command.activity();
        if (activity.getId() == null || activity.getId().isBlank()) {
            throw InvalidArgumentException.required("activity.id");
        }

        log.debug("Updating activity {}", activity.getId());

        Itinerary itinerary = itineraryRepository
                .findByActivityId(activity.getId())
                .orElseThrow(() -> new NotFoundException("Activity", activity.getId()));

        Activity updated = itinerary.replaceActivity(activity);

        itineraryRepository.save(itinerary);
        log.info("Updated activity {} in itinerary {}", activity.getId(), itinerary.getId());
        return updated;
    }
}
