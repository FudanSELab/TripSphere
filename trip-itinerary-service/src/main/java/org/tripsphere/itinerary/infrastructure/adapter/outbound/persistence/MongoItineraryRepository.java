package org.tripsphere.itinerary.infrastructure.adapter.outbound.persistence;

import org.springframework.data.mongodb.repository.MongoRepository;
import org.tripsphere.itinerary.infrastructure.adapter.outbound.persistence.document.ItineraryDocument;

public interface MongoItineraryRepository
        extends MongoRepository<ItineraryDocument, String>, CustomMongoItineraryRepository {}
