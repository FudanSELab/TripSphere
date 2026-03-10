package org.tripsphere.hotel.mapper;

import java.util.List;
import org.mapstruct.*;
import org.mapstruct.factory.Mappers;
import org.tripsphere.hotel.model.HotelDoc;
import org.tripsphere.hotel.model.HotelInformation;
import org.tripsphere.hotel.v1.Hotel;

@Mapper(
        collectionMappingStrategy = CollectionMappingStrategy.ADDER_PREFERRED,
        unmappedTargetPolicy = ReportingPolicy.IGNORE,
        nullValueCheckStrategy = NullValueCheckStrategy.ALWAYS,
        uses = {CommonMapper.class, MoneyMapper.class})
public interface HotelMapper {
    HotelMapper INSTANCE = Mappers.getMapper(HotelMapper.class);

    HotelDoc toDoc(Hotel hotel);

    Hotel toProto(HotelDoc hotelDoc);

    List<Hotel> toProtoList(List<HotelDoc> hotelDocs);

    // ===================================================================
    // HotelInformation Mappings
    // ===================================================================

    HotelInformation toHotelInformation(org.tripsphere.hotel.v1.HotelInformation proto);

    org.tripsphere.hotel.v1.HotelInformation toHotelInformationProto(HotelInformation doc);
}
