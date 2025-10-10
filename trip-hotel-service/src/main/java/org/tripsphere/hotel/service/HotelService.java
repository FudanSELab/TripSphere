package org.tripsphere.hotel.service;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.domain.Example;
import org.springframework.stereotype.Service;
import org.tripsphere.hotel.model.Hotel;
import org.tripsphere.hotel.repository.HotelRepository;

import java.time.format.DateTimeFormatter;
import java.util.Optional;
import java.util.logging.Logger;

@Service
public class HotelService {
    private static final Logger logger = Logger.getLogger(HotelService.class.getName());
    private static final DateTimeFormatter DATE_TIME_FORMATTER =
            DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss");
    private static final DateTimeFormatter DATE_FORMATTER =
            DateTimeFormatter.ofPattern("yyyy-MM-dd");
    @Autowired private HotelRepository hotelRepository;

    public int isExist(String id) {
        Hotel checkHotel = new Hotel();
        checkHotel.setId(id);
        Example<Hotel> projectExample = Example.of(checkHotel);
        long count = hotelRepository.count(projectExample);

        int result = 0;
        if ((int) count != 0) {
            result = 1;
        }
        return result;
    }

    public String addHotel(Hotel hotel) {
        hotelRepository.save(hotel);
        return hotel.getId();
    }

    public void deleteHotel(String id) {
        int exist = this.isExist(id);
        if (exist == 0) {
            return;
        }
        Optional<Hotel> hotelOptional = hotelRepository.findById(id);
        if (hotelOptional.isPresent()) return;
        Hotel hotel = hotelOptional.get();
        hotelRepository.delete(hotel);
    }

    public void changHotel(Hotel hotel) {
        int exist = this.isExist(hotel.getId());
        if (exist == 0) return;
        Optional<Hotel> hotelOptionalOld = hotelRepository.findById(hotel.getId());
        if (hotelOptionalOld.isPresent()) return;
        Hotel hotelOld = hotelOptionalOld.get();
        hotelOld.setName(hotel.getName());
        hotelOld.setCountry(hotel.getCountry());
        hotelOld.setProvince(hotel.getCountry());
        hotelOld.setCity(hotel.getCity());
        hotelOld.setAddress(hotel.getAddress());
        hotelOld.setZone(hotel.getZone());
        hotelOld.setIntroduction(hotel.getIntroduction());
        hotelOld.setTags(hotel.getTags());
        hotelOld.setRooms(hotel.getRooms());
        return;
    }
}
