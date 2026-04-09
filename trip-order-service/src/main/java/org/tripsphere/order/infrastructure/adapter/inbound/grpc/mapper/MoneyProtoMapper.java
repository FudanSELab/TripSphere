package org.tripsphere.order.infrastructure.adapter.inbound.grpc.mapper;

import org.mapstruct.CollectionMappingStrategy;
import org.mapstruct.Mapper;
import org.mapstruct.MappingConstants;
import org.mapstruct.NullValueCheckStrategy;
import org.tripsphere.order.domain.model.Money;

@Mapper(
        componentModel = MappingConstants.ComponentModel.SPRING,
        collectionMappingStrategy = CollectionMappingStrategy.ADDER_PREFERRED,
        nullValueCheckStrategy = NullValueCheckStrategy.ALWAYS)
public interface MoneyProtoMapper {

    default org.tripsphere.common.v1.Money toProto(Money domain) {
        if (domain == null) {
            return org.tripsphere.common.v1.Money.getDefaultInstance();
        }
        return org.tripsphere.common.v1.Money.newBuilder()
                .setCurrency(domain.currency())
                .setUnits(domain.units())
                .setNanos(domain.nanos())
                .build();
    }

    default Money toDomain(org.tripsphere.common.v1.Money proto) {
        if (proto == null || proto.equals(org.tripsphere.common.v1.Money.getDefaultInstance())) {
            return null;
        }
        return new Money(proto.getCurrency(), proto.getUnits(), proto.getNanos());
    }
}
