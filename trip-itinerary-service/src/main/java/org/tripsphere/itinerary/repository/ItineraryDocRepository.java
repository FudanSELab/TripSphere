package org.tripsphere.itinerary.repository;

import org.springframework.data.mongodb.repository.MongoRepository;
import org.tripsphere.itinerary.model.ItineraryDoc;

public interface ItineraryDocRepository extends MongoRepository<ItineraryDoc, String>, CustomItineraryDocRepository {}
