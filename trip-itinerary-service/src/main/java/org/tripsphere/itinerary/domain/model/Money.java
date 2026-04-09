package org.tripsphere.itinerary.domain.model;

import java.math.BigDecimal;
import java.util.Currency;
import java.util.Objects;

public record Money(Currency currency, BigDecimal amount) {
    public Money {
        Objects.requireNonNull(currency, "currency cannot be null");
        Objects.requireNonNull(amount, "amount cannot be null");
    }
}
