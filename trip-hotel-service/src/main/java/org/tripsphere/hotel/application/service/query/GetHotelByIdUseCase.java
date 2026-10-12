package org.tripsphere.hotel.application.service.query;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.tripsphere.hotel.application.exception.NotFoundException;
import org.tripsphere.hotel.application.port.HotelRepository;
import org.tripsphere.hotel.domain.model.Hotel;

@Slf4j
@Service
@RequiredArgsConstructor
public class GetHotelByIdUseCase {

    private final HotelRepository hotelRepository;

    public Hotel execute(String id) {
        Hotel hotel = hotelRepository.findById(id)
                .orElseThrow(() -> new NotFoundException("Hotel", id));
        log.info("Loaded hotel by id: id={}", id);
        return hotel;
    }
}
