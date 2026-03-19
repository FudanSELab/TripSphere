package org.tripsphere.inventory.domain.exception;

import lombok.Getter;

@Getter
public class InsufficientStockException extends InventoryDomainException {

    private final String skuId;
    private final String date;
    private final int requested;
    private final int available;

    public InsufficientStockException(String skuId, String date, int requested, int available) {
        super(String.format(
                "Insufficient inventory for SKU '%s' on %s: requested=%d, available=%d",
                skuId, date, requested, available));
        this.skuId = skuId;
        this.date = date;
        this.requested = requested;
        this.available = available;
    }
}
