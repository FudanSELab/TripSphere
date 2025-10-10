package org.tripsphere.hotel.dao;

import org.tripsphere.hotel.model.Hotel;
import org.springframework.stereotype.Repository;
import org.springframework.data.mongodb.repository.MongoRepository;

import java.util.Optional;

@Repository
public interface HotelDao extends MongoRepository<Hotel, String> {
    public Optional<Hotel> findById(String id);
}
