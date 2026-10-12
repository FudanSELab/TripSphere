package org.tripsphere.hotel.application.service.query;

import java.util.List;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.tripsphere.hotel.application.exception.NotFoundException;
import org.tripsphere.hotel.application.port.HotelRepository;
import org.tripsphere.hotel.application.port.RoomTypeRepository;
import org.tripsphere.hotel.domain.model.RoomType;

@Slf4j
@Service
@RequiredArgsConstructor
public class GetRoomTypesByHotelIdUseCase {

    private final HotelRepository hotelRepository;
    private final RoomTypeRepository roomTypeRepository;

    public List<RoomType> execute(String hotelId) {
        hotelRepository.findById(hotelId).orElseThrow(() -> new NotFoundException("Hotel", hotelId));
        List<RoomType> roomTypes = roomTypeRepository.findByHotelId(hotelId);
        log.info(
                "Listed room types by hotel: hotelId={}, resultCount={}",
                hotelId,
                roomTypes.size());
        return roomTypes;
    }
}
