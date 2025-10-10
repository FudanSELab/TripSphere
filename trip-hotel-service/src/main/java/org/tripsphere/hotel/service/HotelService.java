package org.tripsphere.hotel.service;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.domain.Example;
import org.springframework.stereotype.Service;
import org.tripsphere.hotel.dao.HotelDao;
import org.tripsphere.hotel.model.Hotel;

import java.time.format.DateTimeFormatter;
import java.util.Optional;
import java.util.logging.Logger;

@Service
public class HotelService {
    private static final Logger logger = Logger.getLogger(HotelService.class.getName());
    // 定义日期时间格式，假设数据库中存储的是这种格式
    private static final DateTimeFormatter DATE_TIME_FORMATTER =
            DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss");
    private static final DateTimeFormatter DATE_FORMATTER =
            DateTimeFormatter.ofPattern("yyyy-MM-dd");
    @Autowired private HotelDao hotelDao;

    public int isExist(String id) {
        Hotel checkHotel = new Hotel();
        checkHotel.setId(id);
        Example<Hotel> projectExample = Example.of(checkHotel);
        long count = hotelDao.count(projectExample);

        int result = 0;
        if ((int) count != 0) {
            result = 1;
        }
        return result;
    }

    public String addHotel(Hotel hotel) {
        hotelDao.save(hotel);
        return hotel.getId();
    }

    public void deleteHotel(String id) {
        int exist = this.isExist(id);
        if (exist == 0) {
            return;
        }
        Optional<Hotel> hotelOptional = hotelDao.findById(id);
        if (hotelOptional.isPresent()) return;
        Hotel hotel = hotelOptional.get();
        hotelDao.delete(hotel);
    }

    public void changHotel(Hotel hotel) {
        int exist = this.isExist(hotel.getId());
        if (exist == 0) return;
        Optional<Hotel> hotelOptionalOld = hotelDao.findById(hotel.getId());
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
