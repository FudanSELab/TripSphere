package org.tripsphere.itinerary.infrastructure.adapter.inbound.grpc.mapper;

import java.math.BigDecimal;
import java.util.Currency;
import org.mapstruct.Mapper;
import org.mapstruct.NullValueCheckStrategy;
import org.mapstruct.ReportingPolicy;
import org.tripsphere.itinerary.domain.model.Money;

@Mapper(
        componentModel = "spring",
        unmappedTargetPolicy = ReportingPolicy.IGNORE,
        nullValueCheckStrategy = NullValueCheckStrategy.ALWAYS)
public interface MoneyProtoMapper {

    default Money toDomain(org.tripsphere.common.v1.Money proto) {
        if (proto == null || proto.equals(org.tripsphere.common.v1.Money.getDefaultInstance())) return null;
        Currency currency = Currency.getInstance(proto.getCurrency());
        BigDecimal amount = BigDecimal.valueOf(proto.getUnits()).add(BigDecimal.valueOf(proto.getNanos(), 9));
        return new Money(currency, amount);
    }

    default org.tripsphere.common.v1.Money toProto(Money money) {
        if (money == null) return org.tripsphere.common.v1.Money.getDefaultInstance();
        org.tripsphere.common.v1.Money.Builder builder = org.tripsphere.common.v1.Money.newBuilder();
        if (money.currency() != null) {
            builder.setCurrency(money.currency().getCurrencyCode());
        }
        if (money.amount() != null) {
            long units = money.amount().longValue();
            int nanos =
                    money.amount().remainder(BigDecimal.ONE).movePointRight(9).intValue();
            builder.setUnits(units);
            builder.setNanos(nanos);
        }
        return builder.build();
    }
}
