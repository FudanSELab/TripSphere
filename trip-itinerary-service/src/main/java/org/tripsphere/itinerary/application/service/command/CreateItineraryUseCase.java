package org.tripsphere.itinerary.application.service.command;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.tripsphere.itinerary.application.dto.CreateItineraryCommand;
import org.tripsphere.itinerary.application.port.ItineraryRepository;
import org.tripsphere.itinerary.domain.model.Itinerary;

@Slf4j
@Service
@RequiredArgsConstructor
public class CreateItineraryUseCase {

    private final ItineraryRepository itineraryRepository;

    public Itinerary execute(CreateItineraryCommand command) {
        log.debug("Creating itinerary for user: {}", command.userId());

        Itinerary itinerary = Itinerary.builder()
                .userId(command.userId())
                .title(command.title())
                .destinationPoiId(command.destinationPoiId())
                .destinationName(command.destinationName())
                .startDate(command.startDate())
                .endDate(command.endDate())
                .dayPlans(command.dayPlans())
                .metadata(command.metadata())
                .summary(command.summary())
                .markdownContent(command.markdownContent())
                .build();

        itinerary.ensureAllIds();

        Itinerary saved = itineraryRepository.save(itinerary);
        log.info("Created itinerary with id: {}", saved.getId());
        return saved;
    }
}
