package org.tripsphere.itinerary.mapper;

import org.mapstruct.AfterMapping;
import org.mapstruct.CollectionMappingStrategy;
import org.mapstruct.Mapper;
import org.mapstruct.Mapping;
import org.mapstruct.MappingTarget;
import org.mapstruct.NullValueCheckStrategy;
import org.mapstruct.ReportingPolicy;
import org.mapstruct.factory.Mappers;
import org.tripsphere.itinerary.model.ItinerarySummaryDoc;
import org.tripsphere.itinerary.v1.ItinerarySummary;

@Mapper(
        collectionMappingStrategy = CollectionMappingStrategy.ADDER_PREFERRED,
        unmappedTargetPolicy = ReportingPolicy.IGNORE,
        nullValueCheckStrategy = NullValueCheckStrategy.ALWAYS,
        uses = MoneyMapper.class)
public interface ItinerarySummaryMapper {
    ItinerarySummaryMapper INSTANCE = Mappers.getMapper(ItinerarySummaryMapper.class);

    @Mapping(target = "totalEstimatedCost", ignore = true)
    ItinerarySummaryDoc toDoc(ItinerarySummary summary);

    @AfterMapping
    default void setMoneyFromProto(@MappingTarget ItinerarySummaryDoc doc, ItinerarySummary summary) {
        if (summary != null && summary.hasTotalEstimatedCost()) {
            doc.setTotalEstimatedCost(MoneyMapper.INSTANCE.toMoney(summary.getTotalEstimatedCost()));
        }
    }

    @Mapping(target = "totalEstimatedCost", ignore = true)
    ItinerarySummary toProto(ItinerarySummaryDoc doc);

    @AfterMapping
    default void setMoneyFromDoc(@MappingTarget ItinerarySummary.Builder builder, ItinerarySummaryDoc doc) {
        if (doc != null && doc.getTotalEstimatedCost() != null) {
            builder.setTotalEstimatedCost(MoneyMapper.INSTANCE.toMoneyProto(doc.getTotalEstimatedCost()));
        }
    }
}
