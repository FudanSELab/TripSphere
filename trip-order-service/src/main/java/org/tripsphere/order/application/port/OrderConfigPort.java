package org.tripsphere.order.application.port;

public interface OrderConfigPort {

    int expireSeconds();

    int dedupWindowSeconds();

    int expiryBatchSize();
}
