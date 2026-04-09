package org.tripsphere.poi.application.service.command;

import com.github.f4b6a3.uuid.UuidCreator;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.tripsphere.poi.application.dto.CreatePoiCommand;
import org.tripsphere.poi.application.port.PoiRepository;
import org.tripsphere.poi.domain.model.Poi;

@Slf4j
@Service
@RequiredArgsConstructor
public class CreatePoiUseCase {

    private final PoiRepository poiRepository;

    public Poi execute(CreatePoiCommand command) {
        log.debug("Creating POI: {}", command.name());
        Poi poi = buildPoi(command);
        Poi saved = poiRepository.save(poi);
        log.info("Created POI with id: {}", saved.getId());
        return saved;
    }

    Poi buildPoi(CreatePoiCommand command) {
        return Poi.create(
                UuidCreator.getTimeOrderedEpoch().toString(),
                command.name(),
                command.location(),
                command.address(),
                command.adcode(),
                command.amapId(),
                command.categories(),
                command.images());
    }
}
