package org.tripsphere.product.domain.exception;

import lombok.Getter;

@Getter
public class ProductDomainException extends RuntimeException {

    public ProductDomainException(String message) {
        super(message);
    }

    public ProductDomainException(String message, Throwable cause) {
        super(message, cause);
    }
}
