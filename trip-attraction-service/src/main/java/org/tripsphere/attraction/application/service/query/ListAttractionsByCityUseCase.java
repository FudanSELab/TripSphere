package org.tripsphere.attraction.application.service.query;

import java.util.List;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.tripsphere.attraction.application.port.AttractionRepository;
import org.tripsphere.attraction.domain.model.Attraction;

@Service
@RequiredArgsConstructor
public class ListAttractionsByCityUseCase {

    private static final int DEFAULT_PAGE_SIZE = 12;

    private final AttractionRepository attractionRepository;

    public List<Attraction> execute(String city, List<String> tags, int pageSize, String pageToken) {
        int effectivePageSize = pageSize > 0 ? pageSize : DEFAULT_PAGE_SIZE;
        int skip = 0;
        if (pageToken != null && !pageToken.isEmpty()) {
            try {
                skip = Integer.parseInt(pageToken);
            } catch (NumberFormatException ignored) {
                skip = 0;
            }
        }
        return attractionRepository.listByCity(city, tags.isEmpty() ? null : tags, effectivePageSize, skip);
    }
}
