package org.tripsphere.product.infrastructure.adapter.inbound.grpc.mapper;

import java.util.List;
import org.mapstruct.CollectionMappingStrategy;
import org.mapstruct.Mapper;
import org.mapstruct.MappingConstants;
import org.mapstruct.NullValueCheckStrategy;
import org.mapstruct.ValueMapping;
import org.tripsphere.product.domain.model.Sku;
import org.tripsphere.product.domain.model.SkuStatus;

@Mapper(
        componentModel = MappingConstants.ComponentModel.SPRING,
        collectionMappingStrategy = CollectionMappingStrategy.ADDER_PREFERRED,
        nullValueCheckStrategy = NullValueCheckStrategy.ALWAYS,
        uses = {MoneyProtoMapper.class, StructProtoMapper.class})
public interface SkuProtoMapper {

    // Domain -> Proto

    @ValueMapping(source = "UNSPECIFIED", target = "SKU_STATUS_UNSPECIFIED")
    @ValueMapping(source = "ACTIVE", target = "SKU_STATUS_ACTIVE")
    @ValueMapping(source = "INACTIVE", target = "SKU_STATUS_INACTIVE")
    org.tripsphere.product.v1.SkuStatus mapSkuStatus(SkuStatus skuStatus);

    org.tripsphere.product.v1.Sku map(Sku sku);

    List<org.tripsphere.product.v1.Sku> mapToProtos(List<Sku> skus);

    // Proto -> Domain

    @ValueMapping(source = "SKU_STATUS_UNSPECIFIED", target = "UNSPECIFIED")
    @ValueMapping(source = "SKU_STATUS_ACTIVE", target = "ACTIVE")
    @ValueMapping(source = "SKU_STATUS_INACTIVE", target = "INACTIVE")
    @ValueMapping(source = MappingConstants.ANY_REMAINING, target = "UNSPECIFIED")
    SkuStatus mapSkuStatusToDomain(org.tripsphere.product.v1.SkuStatus protoStatus);

    Sku mapToDomain(org.tripsphere.product.v1.Sku proto);
}
