package org.tripsphere.order.domain.exception;

import lombok.Getter;

@Getter
public class InvalidOrderStateException extends OrderDomainException {

    private final String orderId;
    private final String currentStatus;
    private final String attemptedAction;

    public InvalidOrderStateException(String orderId, String currentStatus, String attemptedAction) {
        super(String.format("Order '%s' is in status '%s', cannot %s", orderId, currentStatus, attemptedAction));
        this.orderId = orderId;
        this.currentStatus = currentStatus;
        this.attemptedAction = attemptedAction;
    }
}
