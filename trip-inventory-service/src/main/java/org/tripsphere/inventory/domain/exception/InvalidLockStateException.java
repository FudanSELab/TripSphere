package org.tripsphere.inventory.domain.exception;

import lombok.Getter;

@Getter
public class InvalidLockStateException extends InventoryDomainException {

    private final String lockId;
    private final String currentStatus;
    private final String attemptedAction;

    public InvalidLockStateException(String lockId, String currentStatus, String attemptedAction) {
        super(String.format("Lock '%s' is in status '%s', cannot %s", lockId, currentStatus, attemptedAction));
        this.lockId = lockId;
        this.currentStatus = currentStatus;
        this.attemptedAction = attemptedAction;
    }
}
