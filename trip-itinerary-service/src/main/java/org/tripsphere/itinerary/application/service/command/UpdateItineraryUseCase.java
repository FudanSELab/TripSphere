package org.tripsphere.itinerary.application.service.command;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.tripsphere.itinerary.application.dto.UpdateItineraryCommand;
import org.tripsphere.itinerary.application.exception.InvalidArgumentException;
import org.tripsphere.itinerary.application.exception.NotFoundException;
import org.tripsphere.itinerary.application.port.ItineraryRepository;
import org.tripsphere.itinerary.domain.model.Itinerary;

@Slf4j
@Service
@RequiredArgsConstructor
public class UpdateItineraryUseCase {

    private final ItineraryRepository itineraryRepository;

    public Itinerary execute(UpdateItineraryCommand command) {
        if (command.id() == null || command.id().isBlank()) {
            throw InvalidArgumentException.required("itinerary.id");
        }

        log.debug("Updating itinerary meta: {}", command.id());

        Itinerary itinerary = itineraryRepository
                .findById(command.id())
                .orElseThrow(() -> new NotFoundException("Itinerary", command.id()));

        itinerary.updateMetadata(
                command.title(),
                command.startDate(),
                command.endDate(),
                command.destinationName(),
                command.markdownContent(),
                command.summary());

        Itinerary saved = itineraryRepository.save(itinerary);
        log.info("Updated itinerary meta for id: {}", saved.getId());
        return saved;
    }
}
