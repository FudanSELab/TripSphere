package org.tripsphere.order.adapter.inbound.grpc.mapper;

import java.time.LocalDate;
import org.mapstruct.CollectionMappingStrategy;
import org.mapstruct.Mapper;
import org.mapstruct.MappingConstants;
import org.mapstruct.NullValueCheckStrategy;
import org.tripsphere.common.v1.Date;

@Mapper(
        componentModel = MappingConstants.ComponentModel.SPRING,
        collectionMappingStrategy = CollectionMappingStrategy.ADDER_PREFERRED,
        nullValueCheckStrategy = NullValueCheckStrategy.ALWAYS)
public interface DateProtoMapper {

    default LocalDate toDomain(Date proto) {
        if (proto == null) return null;
        if (proto.getYear() == 0 && proto.getMonth() == 0 && proto.getDay() == 0) return null;
        return LocalDate.of(proto.getYear(), proto.getMonth(), proto.getDay());
    }

    default Date toProto(LocalDate date) {
        if (date == null) return Date.getDefaultInstance();
        return Date.newBuilder()
                .setYear(date.getYear())
                .setMonth(date.getMonthValue())
                .setDay(date.getDayOfMonth())
                .build();
    }
}
