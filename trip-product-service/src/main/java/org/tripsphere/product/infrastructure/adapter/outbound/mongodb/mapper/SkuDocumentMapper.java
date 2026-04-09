package org.tripsphere.product.infrastructure.adapter.outbound.mongodb.mapper;

import org.mapstruct.Mapper;
import org.mapstruct.MappingConstants;
import org.mapstruct.NullValueCheckStrategy;
import org.mapstruct.ValueMapping;
import org.tripsphere.product.domain.model.Sku;
import org.tripsphere.product.domain.model.SkuStatus;
import org.tripsphere.product.infrastructure.adapter.outbound.mongodb.document.SkuDocument;

@Mapper(componentModel = MappingConstants.ComponentModel.SPRING, nullValueCheckStrategy = NullValueCheckStrategy.ALWAYS)
public interface SkuDocumentMapper {
    String mapSkuStatus(SkuStatus skuStatus);

    @ValueMapping(source = MappingConstants.ANY_REMAINING, target = "UNSPECIFIED")
    SkuStatus mapSkuStatus(String skuStatus);

    SkuDocument map(Sku sku);

    Sku map(SkuDocument doc);
}
