package org.tripsphere.hotel.infrastructure.adapter.outbound.persistence;

import java.util.Optional;
import org.springframework.data.mongodb.repository.MongoRepository;
import org.tripsphere.hotel.infrastructure.adapter.outbound.persistence.document.HotelDocument;

public interface HotelMongoRepository extends MongoRepository<HotelDocument, String> {

    Optional<HotelDocument> findByPoiId(String poiId);
}
