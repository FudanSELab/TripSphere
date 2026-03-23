package org.tripsphere.product.adapter.outbound.mongodb.mapper;

import org.mapstruct.Mapper;
import org.mapstruct.MappingConstants;
import org.mapstruct.NullValueCheckStrategy;
import org.mapstruct.ValueMapping;
import org.tripsphere.product.adapter.outbound.mongodb.document.SkuDocument;
import org.tripsphere.product.domain.model.Sku;
import org.tripsphere.product.domain.model.SkuStatus;

@Mapper(componentModel = MappingConstants.ComponentModel.SPRING, nullValueCheckStrategy = NullValueCheckStrategy.ALWAYS)
public interface SkuDocumentMapper {
    String mapSkuStatus(SkuStatus skuStatus);

    @ValueMapping(source = MappingConstants.ANY_REMAINING, target = "UNSPECIFIED")
    SkuStatus mapSkuStatus(String skuStatus);

    SkuDocument map(Sku sku);

    Sku map(SkuDocument doc);
}
