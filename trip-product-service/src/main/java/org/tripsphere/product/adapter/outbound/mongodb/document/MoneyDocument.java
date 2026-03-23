package org.tripsphere.product.adapter.outbound.mongodb.document;

import java.math.BigDecimal;

public record MoneyDocument(String currency, BigDecimal amount) {
    public MoneyDocument {
        if (currency == null || amount == null) {
            throw new IllegalArgumentException("currency and amount cannot be null");
        }
    }
}
