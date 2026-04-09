package org.tripsphere.product.infrastructure.adapter.outbound.mongodb;

import java.util.List;
import java.util.Optional;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Sort;
import org.springframework.data.mongodb.core.MongoTemplate;
import org.springframework.data.mongodb.core.query.Criteria;
import org.springframework.data.mongodb.core.query.Query;
import org.springframework.stereotype.Repository;
import org.tripsphere.product.application.port.SpuRepository;
import org.tripsphere.product.domain.model.ResourceType;
import org.tripsphere.product.domain.model.Spu;
import org.tripsphere.product.infrastructure.adapter.outbound.mongodb.document.SpuDocument;
import org.tripsphere.product.infrastructure.adapter.outbound.mongodb.mapper.SpuDocumentMapper;

@Repository
@RequiredArgsConstructor
public class SpuRepositoryImpl implements SpuRepository {
    private final SpuDocumentRepository spuDocumentRepository;
    private final MongoTemplate mongoTemplate;
    private final SpuDocumentMapper spuDocumentMapper;

    @Override
    public Spu save(Spu spu) {
        SpuDocument spuDocument = spuDocumentMapper.map(spu);
        SpuDocument saved = spuDocumentRepository.save(spuDocument);
        return spuDocumentMapper.map(saved);
    }

    @Override
    public List<Spu> saveAll(List<Spu> spus) {
        List<SpuDocument> spuDocuments = spuDocumentMapper.mapToDocuments(spus);
        List<SpuDocument> saved = spuDocumentRepository.saveAll(spuDocuments);
        return spuDocumentMapper.mapToDomains(saved);
    }

    @Override
    public Optional<Spu> findById(String id) {
        return spuDocumentRepository.findById(id).map(spuDocumentMapper::map);
    }

    @Override
    public List<Spu> findAllById(List<String> ids) {
        List<SpuDocument> spuDocuments = spuDocumentRepository.findAllById(ids);
        return spuDocumentMapper.mapToDomains(spuDocuments);
    }

    @Override
    public boolean existsById(String id) {
        return spuDocumentRepository.existsById(id);
    }

    @Override
    public Optional<Spu> findBySkuId(String skuId) {
        return spuDocumentRepository.findBySkuId(skuId).map(spuDocumentMapper::map);
    }

    @Override
    public List<Spu> findBySkuIds(List<String> skuIds) {
        List<SpuDocument> spuDocuments = spuDocumentRepository.findBySkuIdIn(skuIds);
        return spuDocumentMapper.mapToDomains(spuDocuments);
    }

    @Override
    public List<Spu> findByResource(ResourceType resourceType, String resourceId, int limit, String afterId) {
        String resourceTypeStr = spuDocumentMapper.mapResourceType(resourceType);

        Criteria criteria = Criteria.where("resourceType")
                .is(resourceTypeStr)
                .and("resourceId")
                .is(resourceId);
        if (afterId != null) {
            criteria = criteria.and("_id").gt(afterId);
        }
        Query query =
                new Query(criteria).with(Sort.by(Sort.Direction.ASC, "_id")).limit(limit);
        List<SpuDocument> docs = mongoTemplate.find(query, SpuDocument.class);
        return spuDocumentMapper.mapToDomains(docs);
    }
}
