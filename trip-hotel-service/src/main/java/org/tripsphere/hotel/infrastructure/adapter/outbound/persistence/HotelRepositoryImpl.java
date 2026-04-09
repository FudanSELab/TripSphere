package org.tripsphere.hotel.infrastructure.adapter.outbound.persistence;

import java.time.Instant;
import java.util.List;
import java.util.Optional;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Sort;
import org.springframework.data.geo.Point;
import org.springframework.data.mongodb.core.MongoTemplate;
import org.springframework.data.mongodb.core.query.Criteria;
import org.springframework.data.mongodb.core.query.Query;
import org.springframework.stereotype.Component;
import org.tripsphere.hotel.application.port.HotelRepository;
import org.tripsphere.hotel.domain.model.GeoLocation;
import org.tripsphere.hotel.domain.model.Hotel;
import org.tripsphere.hotel.infrastructure.adapter.outbound.persistence.document.HotelDocument;
import org.tripsphere.hotel.infrastructure.adapter.outbound.persistence.mapper.HotelDocumentMapper;

@Component
@RequiredArgsConstructor
public class HotelRepositoryImpl implements HotelRepository {

    private final HotelMongoRepository mongoRepository;
    private final MongoTemplate mongoTemplate;
    private final HotelDocumentMapper documentMapper;

    @Override
    public Optional<Hotel> findById(String id) {
        return mongoRepository.findById(id).map(documentMapper::toDomain);
    }

    @Override
    public List<Hotel> findAllByIds(List<String> ids) {
        return documentMapper.toDomainList(mongoRepository.findAllById(ids));
    }

    @Override
    public List<Hotel> findAllByLocationNear(GeoLocation wgs84Location, double radiusMeters, int limit) {
        Criteria criteria = Criteria.where("location")
                .nearSphere(new Point(wgs84Location.longitude(), wgs84Location.latitude()))
                .maxDistance(radiusMeters);
        Query query = new Query(criteria).limit(limit);
        return documentMapper.toDomainList(mongoTemplate.find(query, HotelDocument.class));
    }

    @Override
    public List<Hotel> findByAddressWithPagination(
            String province, String city, int limit, Instant cursorCreatedAt, String cursorId) {
        Criteria criteria = new Criteria();
        if (province != null && !province.isEmpty()) {
            criteria.and("address.province").is(province);
        }
        if (city != null && !city.isEmpty()) {
            criteria.and("address.city").is(city);
        }
        if (cursorCreatedAt != null && cursorId != null) {
            criteria.orOperator(
                    Criteria.where("createdAt").lt(cursorCreatedAt),
                    Criteria.where("createdAt").is(cursorCreatedAt).and("_id").lt(cursorId));
        }
        Query query = new Query(criteria)
                .with(Sort.by(Sort.Direction.DESC, "createdAt").and(Sort.by(Sort.Direction.DESC, "_id")))
                .limit(limit);
        return documentMapper.toDomainList(mongoTemplate.find(query, HotelDocument.class));
    }
}
