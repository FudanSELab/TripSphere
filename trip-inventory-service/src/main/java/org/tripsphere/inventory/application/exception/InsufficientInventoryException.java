package org.tripsphere.inventory.application.exception;

public class InsufficientInventoryException extends BusinessException {

    public InsufficientInventoryException(String skuId, String date, int requested, int available) {
        super(
                String.format(
                        "Insufficient inventory for SKU '%s' on %s: requested=%d, available=%d",
                        skuId, date, requested, available),
                ErrorCode.INSUFFICIENT_INVENTORY);
    }
}
