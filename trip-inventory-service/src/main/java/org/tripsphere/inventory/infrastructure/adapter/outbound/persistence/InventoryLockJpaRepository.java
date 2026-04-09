package org.tripsphere.inventory.infrastructure.adapter.outbound.persistence;

import java.util.Optional;
import org.springframework.data.jpa.repository.JpaRepository;
import org.tripsphere.inventory.infrastructure.adapter.outbound.persistence.entity.InventoryLockEntity;

public interface InventoryLockJpaRepository extends JpaRepository<InventoryLockEntity, String> {

    Optional<InventoryLockEntity> findByLockId(String lockId);

    Optional<InventoryLockEntity> findByOrderId(String orderId);
}
