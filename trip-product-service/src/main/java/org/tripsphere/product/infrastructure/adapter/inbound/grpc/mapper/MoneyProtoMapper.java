package org.tripsphere.product.infrastructure.adapter.inbound.grpc.mapper;

import java.math.BigDecimal;
import java.util.Currency;
import org.mapstruct.CollectionMappingStrategy;
import org.mapstruct.Mapper;
import org.mapstruct.MappingConstants;
import org.mapstruct.NullValueCheckStrategy;
import org.tripsphere.product.domain.model.Money;

@Mapper(
        componentModel = MappingConstants.ComponentModel.SPRING,
        collectionMappingStrategy = CollectionMappingStrategy.ADDER_PREFERRED,
        nullValueCheckStrategy = NullValueCheckStrategy.ALWAYS)
public interface MoneyProtoMapper {
    default Money map(org.tripsphere.common.v1.Money proto) {
        if (proto == null || proto.equals(org.tripsphere.common.v1.Money.getDefaultInstance())) {
            return null;
        }
        return new Money(
                Currency.getInstance(proto.getCurrency()),
                BigDecimal.valueOf(proto.getUnits()).add(BigDecimal.valueOf(proto.getNanos(), 9)));
    }

    default org.tripsphere.common.v1.Money map(Money domain) {
        if (domain == null) {
            return org.tripsphere.common.v1.Money.getDefaultInstance();
        }
        long units = domain.amount().longValue();
        int nanos = domain.amount().remainder(BigDecimal.ONE).movePointRight(9).intValue();
        return org.tripsphere.common.v1.Money.newBuilder()
                .setCurrency(domain.currency().getCurrencyCode())
                .setUnits(units)
                .setNanos(nanos)
                .build();
    }
}
