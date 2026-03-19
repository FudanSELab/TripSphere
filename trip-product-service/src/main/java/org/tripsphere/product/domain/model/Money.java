package org.tripsphere.product.domain.model;

import java.math.BigDecimal;
import java.util.Currency;

public record Money(Currency currency, BigDecimal amount) {
    public Money {
        if (currency == null || amount == null) {
            throw new IllegalArgumentException("currency and amount cannot be null");
        }
    }
}
