package org.tripsphere.hotel.infrastructure.adapter.outbound.persistence.mapper;

import java.util.List;
import org.mapstruct.CollectionMappingStrategy;
import org.mapstruct.Mapper;
import org.mapstruct.NullValueCheckStrategy;
import org.mapstruct.ReportingPolicy;
import org.tripsphere.hotel.domain.model.RoomType;
import org.tripsphere.hotel.infrastructure.adapter.outbound.persistence.document.RoomTypeDocument;

@Mapper(
        componentModel = "spring",
        collectionMappingStrategy = CollectionMappingStrategy.ADDER_PREFERRED,
        unmappedTargetPolicy = ReportingPolicy.IGNORE,
        nullValueCheckStrategy = NullValueCheckStrategy.ALWAYS)
public interface RoomTypeDocumentMapper {

    RoomType toDomain(RoomTypeDocument doc);

    List<RoomType> toDomainList(List<RoomTypeDocument> docs);

    RoomTypeDocument toDocument(RoomType roomType);
}
