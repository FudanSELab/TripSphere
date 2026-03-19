package org.tripsphere.product.domain.exception;

import lombok.Getter;

@Getter
public class InvalidSpuStateException extends ProductDomainException {

    private final String spuId;
    private final String currentStatus;
    private final String attemptedAction;

    public InvalidSpuStateException(String spuId, String currentStatus, String attemptedAction) {
        super(String.format("SPU '%s' is in status '%s', cannot %s", spuId, currentStatus, attemptedAction));
        this.spuId = spuId;
        this.currentStatus = currentStatus;
        this.attemptedAction = attemptedAction;
    }
}
