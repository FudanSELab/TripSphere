package org.tripsphere.order.application.exception;

public class OrderStateException extends BusinessException {

    public OrderStateException(String message) {
        super(message, ErrorCode.ORDER_STATE_CONFLICT);
    }

    public OrderStateException(String orderId, String currentStatus, String requiredStatus) {
        super(
                String.format("Order '%s' is in status '%s', expected '%s'", orderId, currentStatus, requiredStatus),
                ErrorCode.ORDER_STATE_CONFLICT);
    }
}
