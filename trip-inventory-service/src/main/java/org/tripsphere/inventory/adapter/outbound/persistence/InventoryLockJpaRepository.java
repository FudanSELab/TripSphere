package org.tripsphere.inventory.adapter.outbound.persistence;

import java.util.Optional;
import org.springframework.data.jpa.repository.JpaRepository;
import org.tripsphere.inventory.adapter.outbound.persistence.entity.InventoryLockEntity;

public interface InventoryLockJpaRepository extends JpaRepository<InventoryLockEntity, String> {

    Optional<InventoryLockEntity> findByLockId(String lockId);

    Optional<InventoryLockEntity> findByOrderId(String orderId);
}
