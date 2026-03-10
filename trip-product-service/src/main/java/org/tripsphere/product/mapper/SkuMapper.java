package org.tripsphere.product.mapper;

import java.util.List;
import org.mapstruct.AfterMapping;
import org.mapstruct.CollectionMappingStrategy;
import org.mapstruct.Mapper;
import org.mapstruct.MappingTarget;
import org.mapstruct.NullValueCheckStrategy;
import org.mapstruct.ReportingPolicy;
import org.mapstruct.factory.Mappers;
import org.tripsphere.product.model.SkuDoc;
import org.tripsphere.product.v1.Sku;

@Mapper(
        collectionMappingStrategy = CollectionMappingStrategy.ADDER_PREFERRED,
        unmappedTargetPolicy = ReportingPolicy.IGNORE,
        nullValueCheckStrategy = NullValueCheckStrategy.ALWAYS,
        uses = {CommonMapper.class, MoneyMapper.class})
public interface SkuMapper {
    SkuMapper INSTANCE = Mappers.getMapper(SkuMapper.class);

    SkuDoc toDoc(Sku proto);

    List<SkuDoc> toDocList(List<Sku> protos);

    Sku toProto(SkuDoc doc);

    default Sku toProto(SkuDoc doc, String spuId) {
        if (doc == null) {
            return null;
        }
        Sku.Builder builder = toProto(doc).toBuilder();
        if (spuId != null) {
            builder.setSpuId(spuId);
        }
        return builder.build();
    }

    @AfterMapping
    default void normalizeSkuDoc(Sku source, @MappingTarget SkuDoc target) {
        if (source.getId().isEmpty()) {
            target.setId(null);
        }
        if (!source.hasAttributes()) {
            target.setAttributes(null);
        }
        if (source.getStatus() == org.tripsphere.product.v1.SkuStatus.SKU_STATUS_UNSPECIFIED) {
            target.setStatus("SKU_STATUS_ACTIVE");
        }
    }
}
