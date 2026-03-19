package org.tripsphere.inventory.domain.model;

public record Money(String currency, long units, int nanos) {

    public static Money cny(long units, int nanos) {
        return new Money("CNY", units, nanos);
    }
}
