package org.tripsphere.attraction.repository;

import java.util.List;
import java.util.Optional;
import org.springframework.data.domain.Pageable;
import org.springframework.data.mongodb.repository.MongoRepository;
import org.tripsphere.attraction.model.AttractionDoc;

public interface AttractionDocRepository extends MongoRepository<AttractionDoc, String>, CustomAttractionDocRepository {

    Optional<AttractionDoc> findByPoiId(String poiId);

    List<AttractionDoc> findAllByAddressCity(String city, Pageable pageable);

    List<AttractionDoc> findAllByAddressCityAndTagsIn(String city, List<String> tags, Pageable pageable);
}
