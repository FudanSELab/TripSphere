package org.tripsphere.itinerary.mapper;

import java.math.BigDecimal;
import java.util.Currency;
import org.mapstruct.CollectionMappingStrategy;
import org.mapstruct.Mapper;
import org.mapstruct.NullValueCheckStrategy;
import org.mapstruct.ReportingPolicy;
import org.mapstruct.factory.Mappers;
import org.tripsphere.itinerary.model.Money;

@Mapper(
        collectionMappingStrategy = CollectionMappingStrategy.ADDER_PREFERRED,
        unmappedTargetPolicy = ReportingPolicy.IGNORE,
        nullValueCheckStrategy = NullValueCheckStrategy.ALWAYS)
public interface MoneyMapper {
    MoneyMapper INSTANCE = Mappers.getMapper(MoneyMapper.class);

    default Money toMoney(org.tripsphere.common.v1.Money proto) {
        if (proto == null || proto.equals(org.tripsphere.common.v1.Money.getDefaultInstance())) {
            return null;
        }
        Currency currency = Currency.getInstance(proto.getCurrency());
        // Convert units + nanos to BigDecimal
        BigDecimal amount = BigDecimal.valueOf(proto.getUnits()).add(BigDecimal.valueOf(proto.getNanos(), 9));
        return new Money(currency, amount);
    }

    default org.tripsphere.common.v1.Money toMoneyProto(Money obj) {
        if (obj == null) return org.tripsphere.common.v1.Money.getDefaultInstance();
        org.tripsphere.common.v1.Money.Builder builder = org.tripsphere.common.v1.Money.newBuilder();
        if (obj.currency() != null) {
            builder.setCurrency(obj.currency().getCurrencyCode());
        }
        if (obj.amount() != null) {
            // Convert BigDecimal to units + nanos
            long units = obj.amount().longValue();
            int nanos = obj.amount().remainder(BigDecimal.ONE).movePointRight(9).intValue();
            builder.setUnits(units);
            builder.setNanos(nanos);
        }
        return builder.build();
    }
}
