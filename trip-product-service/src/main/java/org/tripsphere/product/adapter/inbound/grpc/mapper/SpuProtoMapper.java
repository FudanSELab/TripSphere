package org.tripsphere.product.adapter.inbound.grpc.mapper;

import java.util.List;
import org.mapstruct.CollectionMappingStrategy;
import org.mapstruct.Mapper;
import org.mapstruct.MappingConstants;
import org.mapstruct.NullValueCheckStrategy;
import org.mapstruct.ValueMapping;
import org.tripsphere.product.domain.model.ResourceType;
import org.tripsphere.product.domain.model.Spu;
import org.tripsphere.product.domain.model.SpuStatus;

@Mapper(
        componentModel = MappingConstants.ComponentModel.SPRING,
        collectionMappingStrategy = CollectionMappingStrategy.ADDER_PREFERRED,
        nullValueCheckStrategy = NullValueCheckStrategy.ALWAYS,
        uses = {SkuProtoMapper.class, StructProtoMapper.class})
public interface SpuProtoMapper {

    // Domain -> Proto

    @ValueMapping(source = "UNSPECIFIED", target = "SPU_STATUS_UNSPECIFIED")
    @ValueMapping(source = "DRAFT", target = "SPU_STATUS_DRAFT")
    @ValueMapping(source = "ON_SHELF", target = "SPU_STATUS_ON_SHELF")
    @ValueMapping(source = "OFF_SHELF", target = "SPU_STATUS_OFF_SHELF")
    org.tripsphere.product.v1.SpuStatus mapSpuStatus(SpuStatus spuStatus);

    @ValueMapping(source = "UNSPECIFIED", target = "RESOURCE_TYPE_UNSPECIFIED")
    @ValueMapping(source = "HOTEL_ROOM", target = "RESOURCE_TYPE_HOTEL_ROOM")
    @ValueMapping(source = "ATTRACTION", target = "RESOURCE_TYPE_ATTRACTION")
    org.tripsphere.product.v1.ResourceType mapResourceType(ResourceType resourceType);

    org.tripsphere.product.v1.Spu map(Spu spu);

    List<org.tripsphere.product.v1.Spu> mapToProtos(List<Spu> spus);

    // Proto -> Domain

    @ValueMapping(source = "SPU_STATUS_UNSPECIFIED", target = "UNSPECIFIED")
    @ValueMapping(source = "SPU_STATUS_DRAFT", target = "DRAFT")
    @ValueMapping(source = "SPU_STATUS_ON_SHELF", target = "ON_SHELF")
    @ValueMapping(source = "SPU_STATUS_OFF_SHELF", target = "OFF_SHELF")
    @ValueMapping(source = MappingConstants.ANY_REMAINING, target = "UNSPECIFIED")
    SpuStatus mapSpuStatusToDomain(org.tripsphere.product.v1.SpuStatus protoStatus);

    @ValueMapping(source = "RESOURCE_TYPE_UNSPECIFIED", target = "UNSPECIFIED")
    @ValueMapping(source = "RESOURCE_TYPE_HOTEL_ROOM", target = "HOTEL_ROOM")
    @ValueMapping(source = "RESOURCE_TYPE_ATTRACTION", target = "ATTRACTION")
    @ValueMapping(source = MappingConstants.ANY_REMAINING, target = "UNSPECIFIED")
    ResourceType mapResourceTypeToDomain(org.tripsphere.product.v1.ResourceType protoResourceType);

    Spu mapToDomain(org.tripsphere.product.v1.Spu proto);

    List<Spu> mapToDomains(List<org.tripsphere.product.v1.Spu> protos);
}
