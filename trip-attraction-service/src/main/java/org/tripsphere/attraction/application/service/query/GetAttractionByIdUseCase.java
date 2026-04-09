package org.tripsphere.attraction.application.service.query;

import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.tripsphere.attraction.application.exception.NotFoundException;
import org.tripsphere.attraction.application.port.AttractionRepository;
import org.tripsphere.attraction.domain.model.Attraction;

@Service
@RequiredArgsConstructor
public class GetAttractionByIdUseCase {

    private final AttractionRepository attractionRepository;

    public Attraction execute(String id) {
        return attractionRepository.findById(id).orElseThrow(() -> new NotFoundException("Attraction", id));
    }
}
