package org.tripsphere.attraction.mapper;

import java.math.BigDecimal;
import java.util.Currency;
import org.mapstruct.*;
import org.mapstruct.factory.Mappers;
import org.tripsphere.attraction.model.Money;

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
        BigDecimal amount = BigDecimal.valueOf(proto.getUnits()).add(BigDecimal.valueOf(proto.getNanos(), 9));
        return new Money(currency, amount);
    }

    default org.tripsphere.common.v1.Money toMoneyProto(Money doc) {
        if (doc == null) return org.tripsphere.common.v1.Money.getDefaultInstance();
        org.tripsphere.common.v1.Money.Builder builder = org.tripsphere.common.v1.Money.newBuilder();
        if (doc.currency() != null) {
            builder.setCurrency(doc.currency().getCurrencyCode());
        }
        if (doc.amount() != null) {
            long units = doc.amount().longValue();
            int nanos = doc.amount().remainder(BigDecimal.ONE).movePointRight(9).intValue();
            builder.setUnits(units);
            builder.setNanos(nanos);
        }
        return builder.build();
    }
}
