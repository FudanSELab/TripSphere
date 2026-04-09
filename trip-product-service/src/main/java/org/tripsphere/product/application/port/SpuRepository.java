package org.tripsphere.product.application.port;

import java.util.List;
import java.util.Optional;
import org.tripsphere.product.domain.model.ResourceType;
import org.tripsphere.product.domain.model.Spu;

public interface SpuRepository {
    Spu save(Spu spu);

    List<Spu> saveAll(List<Spu> spus);

    Optional<Spu> findById(String id);

    List<Spu> findAllById(List<String> ids);

    boolean existsById(String id);

    Optional<Spu> findBySkuId(String skuId);

    List<Spu> findBySkuIds(List<String> skuIds);

    /**
     * Cursor-based pagination: returns up to {@code limit} SPUs for the given resource,
     * with IDs lexicographically greater than {@code afterId} (null for first page),
     * ordered by ID ascending.
     */
    List<Spu> findByResource(ResourceType resourceType, String resourceId, int limit, String afterId);
}
