package org.tripsphere.product.service;

import java.util.List;
import java.util.Optional;
import org.tripsphere.product.v1.Sku;
import org.tripsphere.product.v1.Spu;

public interface ProductService {

    Spu createSpu(Spu spu);

    List<Spu> batchCreateSpus(List<Spu> spus);

    Optional<Spu> getSpuById(String id);

    List<Spu> batchGetSpus(List<String> ids);

    /**
     * List SPUs by resource type and resource ID using cursor-based pagination.
     *
     * @param resourceType the resource type to filter by
     * @param resourceId the resource ID to filter by
     * @param pageSize the maximum number of results per page
     * @param pageToken the page token from the previous request (cursor-based pagination)
     * @return a page result containing SPUs and the next page token
     */
    SpuPage listSpusByResource(
            String resourceType, String resourceId, int pageSize, String pageToken);

    Spu updateSpu(Spu spu, List<String> fieldPaths);

    Optional<Sku> getSkuById(String skuId);

    List<Sku> batchGetSkus(List<String> skuIds);

    /** Represents a paginated result of SPUs. */
    record SpuPage(List<Spu> spus, String nextPageToken) {}
}
