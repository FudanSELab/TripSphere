package org.tripsphere.product.adapter.outbound.mongodb.mapper;

import java.math.BigDecimal;
import java.util.Currency;
import org.mapstruct.Mapper;
import org.mapstruct.Mapping;
import org.mapstruct.MappingConstants;
import org.mapstruct.NullValueCheckStrategy;
import org.mapstruct.ValueMapping;
import org.tripsphere.product.adapter.outbound.mongodb.document.SkuDocument;
import org.tripsphere.product.domain.model.Money;
import org.tripsphere.product.domain.model.Sku;
import org.tripsphere.product.domain.model.SkuStatus;

@Mapper(componentModel = MappingConstants.ComponentModel.SPRING, nullValueCheckStrategy = NullValueCheckStrategy.ALWAYS)
public interface SkuDocumentMapper {
    String mapSkuStatus(SkuStatus skuStatus);

    @ValueMapping(source = MappingConstants.ANY_REMAINING, target = "UNSPECIFIED")
    SkuStatus mapSkuStatus(String skuStatus);

    @Mapping(target = "priceCurrency", source = "basePrice.currency")
    @Mapping(target = "priceAmount", source = "basePrice.amount")
    SkuDocument map(Sku sku);

    @Mapping(target = "basePrice", expression = "java(toMoney(doc.getPriceCurrency(), doc.getPriceAmount()))")
    Sku map(SkuDocument doc);

    default String mapCurrency(Currency currency) {
        return currency != null ? currency.getCurrencyCode() : null;
    }

    default Money toMoney(String currencyCode, BigDecimal amount) {
        if (currencyCode == null || amount == null) return null;
        return new Money(Currency.getInstance(currencyCode), amount);
    }
}
