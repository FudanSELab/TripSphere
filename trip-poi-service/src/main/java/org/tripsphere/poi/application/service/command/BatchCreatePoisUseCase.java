package org.tripsphere.poi.application.service.command;

import java.util.List;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.tripsphere.poi.application.dto.CreatePoiCommand;
import org.tripsphere.poi.application.port.PoiRepository;
import org.tripsphere.poi.domain.model.Poi;

@Slf4j
@Service
@RequiredArgsConstructor
public class BatchCreatePoisUseCase {

    private final PoiRepository poiRepository;
    private final CreatePoiUseCase createPoiUseCase;

    public List<Poi> execute(List<CreatePoiCommand> commands) {
        log.debug("Batch creating {} POIs", commands.size());
        List<Poi> pois = commands.stream().map(createPoiUseCase::buildPoi).toList();
        List<Poi> saved = poiRepository.saveAll(pois);
        log.info("Batch created {} POIs", saved.size());
        return saved;
    }
}
