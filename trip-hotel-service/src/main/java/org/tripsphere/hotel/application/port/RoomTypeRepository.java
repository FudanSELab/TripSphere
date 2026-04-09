package org.tripsphere.hotel.application.port;

import java.util.List;
import org.tripsphere.hotel.domain.model.RoomType;

public interface RoomTypeRepository {

    List<RoomType> findByHotelId(String hotelId);
}
