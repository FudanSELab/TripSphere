package org.tripsphere.hotel.application.service.query;

import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;
import org.tripsphere.hotel.application.exception.NotFoundException;
import org.tripsphere.hotel.application.port.HotelRepository;
import org.tripsphere.hotel.domain.model.Hotel;

@Service
@RequiredArgsConstructor
public class GetHotelByIdUseCase {

    private final HotelRepository hotelRepository;

    public Hotel execute(String id) {
        return hotelRepository.findById(id).orElseThrow(() -> new NotFoundException("Hotel", id));
    }
}
