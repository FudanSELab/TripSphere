package org.tripsphere.product.repository.impl;

import java.time.Instant;
import java.util.List;
import java.util.Optional;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageImpl;
import org.springframework.data.domain.Pageable;
import org.springframework.data.domain.Sort;
import org.springframework.data.mongodb.core.MongoTemplate;
import org.springframework.data.mongodb.core.query.Criteria;
import org.springframework.data.mongodb.core.query.Query;
import org.springframework.data.mongodb.core.query.Update;
import org.springframework.stereotype.Repository;
import org.tripsphere.product.model.SpuDoc;
import org.tripsphere.product.repository.CustomSpuDocRepository;

@Repository
@RequiredArgsConstructor
public class CustomSpuDocRepositoryImpl implements CustomSpuDocRepository {

    private final MongoTemplate mongoTemplate;

    @Override
    public Page<SpuDoc> findByResource(String resourceType, String resourceId, Pageable pageable) {
        Query query = new Query();
        query.addCriteria(
                Criteria.where("resourceType").is(resourceType).and("resourceId").is(resourceId));

        long total = mongoTemplate.count(query, SpuDoc.class);
        query.with(pageable);
        List<SpuDoc> docs = mongoTemplate.find(query, SpuDoc.class);

        return new PageImpl<>(docs, pageable, total);
    }

    @Override
    public List<SpuDoc> findByResourceWithCursor(
            String resourceType,
            String resourceId,
            int limit,
            Instant afterCreatedAt,
            String afterId) {
        Criteria baseCriteria =
                Criteria.where("resourceType").is(resourceType).and("resourceId").is(resourceId);

        Criteria cursorCriteria;
        if (afterCreatedAt != null && afterId != null) {
            // Return documents strictly after the cursor:
            // (createdAt > afterCreatedAt) OR (createdAt == afterCreatedAt AND id > afterId)
            cursorCriteria =
                    new Criteria()
                            .orOperator(
                                    Criteria.where("createdAt").gt(afterCreatedAt),
                                    Criteria.where("createdAt")
                                            .is(afterCreatedAt)
                                            .and("_id")
                                            .gt(afterId));
        } else {
            cursorCriteria = new Criteria();
        }

        Query query =
                new Query(new Criteria().andOperator(baseCriteria, cursorCriteria))
                        .with(Sort.by(Sort.Direction.ASC, "createdAt", "_id"))
                        .limit(limit);

        return mongoTemplate.find(query, SpuDoc.class);
    }

    @Override
    public Optional<SpuDoc> findBySkuId(String skuId) {
        Query query = new Query(Criteria.where("skus.id").is(skuId));
        SpuDoc doc = mongoTemplate.findOne(query, SpuDoc.class);
        return Optional.ofNullable(doc);
    }

    @Override
    public List<SpuDoc> findBySkuIds(List<String> skuIds) {
        Query query = new Query(Criteria.where("skus.id").in(skuIds));
        return mongoTemplate.find(query, SpuDoc.class);
    }

    @Override
    public void updateSpuFields(String id, SpuDoc updates, List<String> fieldPaths) {
        Query query = new Query(Criteria.where("_id").is(id));
        Update update = new Update();

        for (String path : fieldPaths) {
            switch (path) {
                case "name" -> {
                    if (updates.getName() != null) update.set("name", updates.getName());
                }
                case "description" -> {
                    if (updates.getDescription() != null)
                        update.set("description", updates.getDescription());
                }
                case "images" -> {
                    if (updates.getImages() != null) update.set("images", updates.getImages());
                }
                case "status" -> {
                    if (updates.getStatus() != null) update.set("status", updates.getStatus());
                }
                case "attributes" -> {
                    if (updates.getAttributes() != null)
                        update.set("attributes", updates.getAttributes());
                }
                case "skus" -> {
                    if (updates.getSkus() != null) update.set("skus", updates.getSkus());
                }
                default -> {}
            }
        }

        mongoTemplate.updateFirst(query, update, SpuDoc.class);
    }
}
