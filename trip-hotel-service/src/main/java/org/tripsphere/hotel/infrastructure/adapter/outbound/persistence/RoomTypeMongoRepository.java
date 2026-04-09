package org.tripsphere.hotel.infrastructure.adapter.outbound.persistence;

import java.util.List;
import org.springframework.data.mongodb.repository.MongoRepository;
import org.tripsphere.hotel.infrastructure.adapter.outbound.persistence.document.RoomTypeDocument;

public interface RoomTypeMongoRepository extends MongoRepository<RoomTypeDocument, String> {

    List<RoomTypeDocument> findByHotelId(String hotelId);
}
