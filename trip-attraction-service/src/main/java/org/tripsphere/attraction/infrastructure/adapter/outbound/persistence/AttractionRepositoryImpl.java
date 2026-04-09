package org.tripsphere.attraction.infrastructure.adapter.outbound.persistence;

import java.util.List;
import java.util.Optional;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Sort;
import org.springframework.data.geo.Point;
import org.springframework.data.mongodb.core.MongoTemplate;
import org.springframework.data.mongodb.core.query.Criteria;
import org.springframework.data.mongodb.core.query.Query;
import org.springframework.stereotype.Component;
import org.tripsphere.attraction.application.port.AttractionRepository;
import org.tripsphere.attraction.domain.model.Attraction;
import org.tripsphere.attraction.domain.model.GeoLocation;
import org.tripsphere.attraction.infrastructure.adapter.outbound.persistence.document.AttractionDocument;
import org.tripsphere.attraction.infrastructure.adapter.outbound.persistence.mapper.AttractionDocumentMapper;

@Component
@RequiredArgsConstructor
public class AttractionRepositoryImpl implements AttractionRepository {

    private final AttractionMongoRepository mongoRepository;
    private final MongoTemplate mongoTemplate;
    private final AttractionDocumentMapper documentMapper;

    @Override
    public Optional<Attraction> findById(String id) {
        return mongoRepository.findById(id).map(documentMapper::toDomain);
    }

    @Override
    public List<Attraction> findAllByIds(List<String> ids) {
        return documentMapper.toDomainList(mongoRepository.findAllById(ids));
    }

    @Override
    public Optional<Attraction> findByPoiId(String poiId) {
        return mongoRepository.findByPoiId(poiId).map(documentMapper::toDomain);
    }

    @Override
    public List<Attraction> findAllByLocationNear(
            GeoLocation wgs84Location, double radiusMeters, int limit, List<String> tags) {
        Criteria criteria = Criteria.where("location")
                .nearSphere(new Point(wgs84Location.longitude(), wgs84Location.latitude()))
                .maxDistance(radiusMeters);
        if (tags != null && !tags.isEmpty()) {
            criteria.and("tags").in(tags);
        }
        Query query = new Query(criteria).with(PageRequest.of(0, limit));
        List<AttractionDocument> docs = mongoTemplate.find(query, AttractionDocument.class);
        return documentMapper.toDomainList(docs);
    }

    @Override
    public List<Attraction> listByCity(String city, List<String> tags, int pageSize, int skip) {
        int page = pageSize > 0 ? skip / pageSize : 0;
        PageRequest pageRequest = PageRequest.of(page, pageSize, Sort.by("name"));
        List<AttractionDocument> docs;
        if (tags == null || tags.isEmpty()) {
            docs = mongoRepository.findAllByAddressCity(city, pageRequest);
        } else {
            docs = mongoRepository.findAllByAddressCityAndTagsIn(city, tags, pageRequest);
        }
        return documentMapper.toDomainList(docs);
    }
}
