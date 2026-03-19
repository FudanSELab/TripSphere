package org.tripsphere.order.domain.model;

public record Money(String currency, long units, int nanos) {

    public static Money cny(long units, int nanos) {
        return new Money("CNY", units, nanos);
    }

    public static Money zero() {
        return new Money("CNY", 0, 0);
    }
}
