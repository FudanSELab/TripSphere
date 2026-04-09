package org.tripsphere.product.domain.exception;

import lombok.Getter;

@Getter
public class InvalidSkuStateException extends ProductDomainException {

    private final String skuId;
    private final String currentStatus;
    private final String attemptedAction;

    public InvalidSkuStateException(String skuId, String currentStatus, String attemptedAction) {
        super(String.format("SKU '%s' is in status '%s', cannot %s", skuId, currentStatus, attemptedAction));
        this.skuId = skuId;
        this.currentStatus = currentStatus;
        this.attemptedAction = attemptedAction;
    }
}
