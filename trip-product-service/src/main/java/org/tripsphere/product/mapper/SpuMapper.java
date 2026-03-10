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
import org.tripsphere.product.model.SpuDoc;
import org.tripsphere.product.v1.Spu;
import org.tripsphere.product.v1.SpuStatus;

@Mapper(
        collectionMappingStrategy = CollectionMappingStrategy.ADDER_PREFERRED,
        unmappedTargetPolicy = ReportingPolicy.IGNORE,
        nullValueCheckStrategy = NullValueCheckStrategy.ALWAYS,
        uses = {CommonMapper.class, MoneyMapper.class, SkuMapper.class})
public interface SpuMapper {
    SpuMapper INSTANCE = Mappers.getMapper(SpuMapper.class);

    SpuDoc toDoc(Spu proto);

    Spu toProto(SpuDoc doc);

    List<Spu> toProtoList(List<SpuDoc> docs);

    @AfterMapping
    default void normalizeSpuDoc(Spu source, @MappingTarget SpuDoc target) {
        if (source.getId().isEmpty()) {
            target.setId(null);
        }
        if (source.getImagesList().isEmpty()) {
            target.setImages(null);
        }
        if (source.getSkusList().isEmpty()) {
            target.setSkus(null);
        }
        if (!source.hasAttributes()) {
            target.setAttributes(null);
        }
        if (source.getStatus() == SpuStatus.SPU_STATUS_UNSPECIFIED) {
            target.setStatus("SPU_STATUS_DRAFT");
        }
    }

    @AfterMapping
    default void fillSkus(SpuDoc source, @MappingTarget Spu.Builder target) {
        target.clearSkus();
        if (source.getSkus() == null) {
            return;
        }
        for (SkuDoc skuDoc : source.getSkus()) {
            target.addSkus(SkuMapper.INSTANCE.toProto(skuDoc, source.getId()));
        }
    }
}
