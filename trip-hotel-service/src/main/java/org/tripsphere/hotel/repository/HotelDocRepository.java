package org.tripsphere.hotel.repository;

import java.util.Optional;
import org.springframework.data.mongodb.repository.MongoRepository;
import org.tripsphere.hotel.model.HotelDoc;

public interface HotelDocRepository extends MongoRepository<HotelDoc, String>, CustomHotelDocRepository {

    Optional<HotelDoc> findByPoiId(String poiId);
}
