package org.tripsphere.product.domain.exception;

import lombok.Getter;

@Getter
public class DuplicateSkuNameException extends ProductDomainException {

    private final String skuName;

    public DuplicateSkuNameException(String skuName) {
        super("SKU name must be unique: '" + skuName + "'");
        this.skuName = skuName;
    }

    public DuplicateSkuNameException() {
        super("SKU names must be unique within an SPU");
        this.skuName = null;
    }
}
