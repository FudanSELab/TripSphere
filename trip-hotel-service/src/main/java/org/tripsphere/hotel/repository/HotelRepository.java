package org.tripsphere.hotel.repository;

import org.springframework.data.mongodb.repository.MongoRepository;
import org.springframework.stereotype.Repository;
import org.tripsphere.hotel.model.Hotel;

import java.util.Optional;

@Repository
public interface HotelRepository extends MongoRepository<Hotel, String> {
    public Optional<Hotel> findById(String id);
}
