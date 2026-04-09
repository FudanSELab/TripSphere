package org.tripsphere.itinerary.infrastructure.adapter.outbound.persistence;

import java.time.Instant;
import java.util.List;
import java.util.Optional;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Repository;
import org.tripsphere.itinerary.application.port.ItineraryRepository;
import org.tripsphere.itinerary.domain.model.Itinerary;
import org.tripsphere.itinerary.infrastructure.adapter.outbound.persistence.document.ItineraryDocument;
import org.tripsphere.itinerary.infrastructure.adapter.outbound.persistence.mapper.ItineraryDocumentMapper;

@Repository
@RequiredArgsConstructor
public class ItineraryRepositoryImpl implements ItineraryRepository {

    private final MongoItineraryRepository mongoRepository;
    private final ItineraryDocumentMapper mapper;

    @Override
    public Itinerary save(Itinerary itinerary) {
        ItineraryDocument document = mapper.toDocument(itinerary);
        ItineraryDocument saved = mongoRepository.save(document);
        return mapper.toDomain(saved);
    }

    @Override
    public Optional<Itinerary> findById(String id) {
        return mongoRepository.findById(id).map(mapper::toDomain);
    }

    @Override
    public Optional<Itinerary> findByActivityId(String activityId) {
        return mongoRepository.findByActivityId(activityId).map(mapper::toDomain);
    }

    @Override
    public List<Itinerary> findByUserIdWithPagination(
            String userId, int limit, Instant cursorCreatedAt, String cursorId) {
        List<ItineraryDocument> documents =
                mongoRepository.findByUserIdWithPagination(userId, limit, cursorCreatedAt, cursorId);
        return mapper.toDomainList(documents);
    }

    @Override
    public boolean existsById(String id) {
        return mongoRepository.existsById(id);
    }

    @Override
    public void deleteById(String id) {
        mongoRepository.deleteById(id);
    }
}
