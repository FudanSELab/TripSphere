package org.tripsphere.inventory.domain.exception;

import lombok.Getter;

@Getter
public class InventoryDomainException extends RuntimeException {

    public InventoryDomainException(String message) {
        super(message);
    }

    public InventoryDomainException(String message, Throwable cause) {
        super(message, cause);
    }
}
