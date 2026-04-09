package org.tripsphere.inventory.application.port;

public interface InventoryConfigPort {
    int defaultLockTimeoutSeconds();

    int lockExpiryBatchSize();
}
