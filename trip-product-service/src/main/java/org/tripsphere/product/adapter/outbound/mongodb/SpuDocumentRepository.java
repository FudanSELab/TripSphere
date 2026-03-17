package org.tripsphere.product.adapter.outbound.mongodb;

import java.util.List;
import java.util.Optional;
import org.springframework.data.mongodb.repository.MongoRepository;
import org.springframework.data.mongodb.repository.Query;
import org.tripsphere.product.adapter.outbound.mongodb.document.SpuDocument;

public interface SpuDocumentRepository extends MongoRepository<SpuDocument, String> {

    @Query("{'skus.id': ?0}")
    Optional<SpuDocument> findBySkuId(String skuId);

    @Query("{'skus.id': {'$in': ?0}}")
    List<SpuDocument> findBySkuIdIn(List<String> skuIds);
}
