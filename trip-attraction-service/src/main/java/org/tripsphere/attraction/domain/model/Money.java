package org.tripsphere.attraction.domain.model;

import java.math.BigDecimal;
import java.util.Currency;
import java.util.Objects;
import org.jspecify.annotations.NonNull;

public record Money(@NonNull Currency currency, @NonNull BigDecimal amount) {
    public Money {
        Objects.requireNonNull(currency, "currency cannot be null");
        Objects.requireNonNull(amount, "amount cannot be null");
    }
}
