package org.tripsphere.attraction.repository;

import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.mongodb.repository.MongoRepository;
import org.springframework.data.mongodb.repository.Query;
import org.springframework.stereotype.Repository;
import org.tripsphere.attraction.model.Attraction;
import org.springframework.data.geo.Distance;
import org.springframework.data.geo.Point;
import org.springframework.data.geo.Circle;

import java.util.List;
import java.util.Optional;

@Repository
public interface AttractionRepository extends MongoRepository<Attraction, String> {
    public Optional<Attraction> findById(String id);


}
