package org.tripsphere.attraction.application.service.query;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.tripsphere.attraction.application.exception.NotFoundException;
import org.tripsphere.attraction.application.port.AttractionRepository;
import org.tripsphere.attraction.domain.model.Attraction;

@Slf4j
@Service
@RequiredArgsConstructor
public class GetAttractionByIdUseCase {

    private final AttractionRepository attractionRepository;

    public Attraction execute(String id) {
        Attraction attraction = attractionRepository.findById(id)
                .orElseThrow(() -> new NotFoundException("Attraction", id));
        log.info("Loaded attraction by id: id={}", id);
        return attraction;
    }
}
