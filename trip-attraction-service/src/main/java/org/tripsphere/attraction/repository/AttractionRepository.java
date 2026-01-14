package org.tripsphere.attraction.repository;

import java.util.Optional;

import org.springframework.data.mongodb.repository.MongoRepository;
import org.springframework.stereotype.Repository;
import org.tripsphere.attraction.model.Attraction;

@Repository
public interface AttractionRepository extends MongoRepository<Attraction, String> {
    public Optional<Attraction> findById(String id);
}
