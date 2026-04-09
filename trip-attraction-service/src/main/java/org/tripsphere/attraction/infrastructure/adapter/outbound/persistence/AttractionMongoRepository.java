package org.tripsphere.attraction.infrastructure.adapter.outbound.persistence;

import java.util.List;
import java.util.Optional;
import org.springframework.data.domain.Pageable;
import org.springframework.data.mongodb.repository.MongoRepository;
import org.tripsphere.attraction.infrastructure.adapter.outbound.persistence.document.AttractionDocument;

public interface AttractionMongoRepository extends MongoRepository<AttractionDocument, String> {

    Optional<AttractionDocument> findByPoiId(String poiId);

    List<AttractionDocument> findAllByAddressCity(String city, Pageable pageable);

    List<AttractionDocument> findAllByAddressCityAndTagsIn(String city, List<String> tags, Pageable pageable);
}
