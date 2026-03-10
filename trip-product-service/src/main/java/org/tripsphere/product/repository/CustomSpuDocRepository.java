package org.tripsphere.product.repository;

import java.time.Instant;
import java.util.List;
import java.util.Optional;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.tripsphere.product.model.SpuDoc;

public interface CustomSpuDocRepository {

    /** Find SPUs by resource type and resource ID with pagination. */
    Page<SpuDoc> findByResource(String resourceType, String resourceId, Pageable pageable);

    /**
     * Find SPUs by resource type and resource ID using cursor-based pagination.
     *
     * @param resourceType the resource type to filter by
     * @param resourceId the resource ID to filter by
     * @param limit maximum number of documents to return
     * @param afterCreatedAt cursor: only return documents created after this instant (nullable)
     * @param afterId cursor: tie-breaker ID for documents with the same createdAt (nullable)
     * @return list of matching SpuDoc documents ordered by createdAt ASC, id ASC
     */
    List<SpuDoc> findByResourceWithCursor(
            String resourceType,
            String resourceId,
            int limit,
            Instant afterCreatedAt,
            String afterId);

    /** Find a SPU that contains a specific SKU ID. */
    Optional<SpuDoc> findBySkuId(String skuId);

    /** Update specific fields of a SPU using field mask. */
    void updateSpuFields(String id, SpuDoc updates, java.util.List<String> fieldPaths);

    /** Find SPUs that contain any of the given SKU IDs. */
    java.util.List<SpuDoc> findBySkuIds(java.util.List<String> skuIds);
}
