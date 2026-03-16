package org.tripsphere.itinerary.mapper;

import java.util.List;
import org.mapstruct.CollectionMappingStrategy;
import org.mapstruct.Mapper;
import org.mapstruct.Mapping;
import org.mapstruct.NullValueCheckStrategy;
import org.mapstruct.ReportingPolicy;
import org.mapstruct.factory.Mappers;
import org.tripsphere.itinerary.model.ItineraryDoc;
import org.tripsphere.itinerary.v1.Itinerary;

@Mapper(
        collectionMappingStrategy = CollectionMappingStrategy.ADDER_PREFERRED,
        unmappedTargetPolicy = ReportingPolicy.IGNORE,
        nullValueCheckStrategy = NullValueCheckStrategy.ALWAYS,
        uses = {CommonMapper.class, ActivityMapper.class, ItinerarySummaryMapper.class})
public interface ItineraryMapper {
    ItineraryMapper INSTANCE = Mappers.getMapper(ItineraryMapper.class);

    // ===================================================================
    // Itinerary Mappings
    // ===================================================================

    /**
     * Convert Itinerary proto to ItineraryDoc. Note: destination POI is converted to just an ID
     * reference.
     *
     * <p>Internal fields (createdAt, updatedAt) are ignored to prevent accidental overwrites —
     * they are managed by Spring Data auditing.
     */
    @Mapping(target = "destinationPoiId", source = "destination.id")
    @Mapping(target = "createdAt", ignore = true)
    @Mapping(target = "updatedAt", ignore = true)
    ItineraryDoc toDoc(Itinerary itinerary);

    /**
     * Convert ItineraryDoc to Itinerary proto. destination POI is NOT hydrated here — only
     * destination_name is populated from the stored plain-text field.
     */
    @Mapping(target = "destination", ignore = true)
    @Mapping(target = "createdAt", source = "createdAt")
    @Mapping(target = "updatedAt", source = "updatedAt")
    Itinerary toProto(ItineraryDoc doc);

    List<Itinerary> toProtoList(List<ItineraryDoc> docs);
}
