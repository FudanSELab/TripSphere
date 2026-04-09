package org.tripsphere.itinerary.application.service.command;

import java.util.ArrayList;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.tripsphere.itinerary.application.dto.ReplaceItineraryCommand;
import org.tripsphere.itinerary.application.exception.NotFoundException;
import org.tripsphere.itinerary.application.port.ItineraryRepository;
import org.tripsphere.itinerary.domain.model.Itinerary;

@Slf4j
@Service
@RequiredArgsConstructor
public class ReplaceItineraryUseCase {

    private final ItineraryRepository itineraryRepository;

    public Itinerary execute(ReplaceItineraryCommand command) {
        log.debug("Replacing itinerary: {}", command.id());

        Itinerary existing = itineraryRepository
                .findById(command.id())
                .orElseThrow(() -> new NotFoundException("Itinerary", command.id()));

        Itinerary replacement = Itinerary.builder()
                .title(command.title())
                .destinationPoiId(command.destinationPoiId())
                .destinationName(command.destinationName())
                .startDate(command.startDate())
                .endDate(command.endDate())
                .dayPlans(command.dayPlans() != null ? new ArrayList<>(command.dayPlans()) : new ArrayList<>())
                .metadata(command.metadata())
                .summary(command.summary())
                .markdownContent(command.markdownContent())
                .build();

        existing.replaceContent(replacement);

        Itinerary saved = itineraryRepository.save(existing);
        log.info("Replaced itinerary with id: {}", saved.getId());
        return saved;
    }
}
