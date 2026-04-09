package org.tripsphere.product.infrastructure.adapter.outbound.mongodb.mapper;

import java.util.List;
import org.mapstruct.Mapper;
import org.mapstruct.MappingConstants;
import org.mapstruct.NullValueCheckStrategy;
import org.mapstruct.ValueMapping;
import org.tripsphere.product.domain.model.ResourceType;
import org.tripsphere.product.domain.model.Spu;
import org.tripsphere.product.domain.model.SpuStatus;
import org.tripsphere.product.infrastructure.adapter.outbound.mongodb.document.SpuDocument;

@Mapper(
        componentModel = MappingConstants.ComponentModel.SPRING,
        nullValueCheckStrategy = NullValueCheckStrategy.ALWAYS,
        uses = {SkuDocumentMapper.class})
public interface SpuDocumentMapper {
    String mapResourceType(ResourceType resourceType);

    @ValueMapping(source = MappingConstants.ANY_REMAINING, target = "UNSPECIFIED")
    ResourceType mapResourceType(String resourceType);

    String mapSpuStatus(SpuStatus spuStatus);

    @ValueMapping(source = MappingConstants.ANY_REMAINING, target = "UNSPECIFIED")
    SpuStatus mapSpuStatus(String spuStatus);

    SpuDocument map(Spu spu);

    Spu map(SpuDocument spuDocument);

    List<SpuDocument> mapToDocuments(List<Spu> spus);

    List<Spu> mapToDomains(List<SpuDocument> spuDocuments);
}
