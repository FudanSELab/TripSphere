package org.tripsphere.inventory.domain.repository;

import java.util.Optional;
import org.tripsphere.inventory.domain.model.InventoryLock;

public interface InventoryLockRepository {

    InventoryLock save(InventoryLock lock);

    Optional<InventoryLock> findByLockId(String lockId);

    Optional<InventoryLock> findByOrderId(String orderId);
}
