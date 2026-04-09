package org.tripsphere.hotel.application.service.query;

import java.util.List;
import java.util.Map;
import java.util.function.Function;
import java.util.stream.Collectors;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.tripsphere.hotel.application.exception.NotFoundException;
import org.tripsphere.hotel.application.port.HotelRepository;
import org.tripsphere.hotel.domain.model.Hotel;

@Service
@RequiredArgsConstructor
public class BatchGetHotelsUseCase {

    private final HotelRepository hotelRepository;

    public List<Hotel> execute(List<String> ids) {
        List<Hotel> hotels = hotelRepository.findAllByIds(ids);

        Map<String, Hotel> byId = hotels.stream().collect(Collectors.toMap(Hotel::getId, Function.identity()));

        List<String> missingIds =
                ids.stream().filter(id -> !byId.containsKey(id)).toList();
        if (!missingIds.isEmpty()) {
            throw new NotFoundException("Hotels with IDs " + missingIds + " not found");
        }

        return ids.stream().map(byId::get).toList();
    }
}
