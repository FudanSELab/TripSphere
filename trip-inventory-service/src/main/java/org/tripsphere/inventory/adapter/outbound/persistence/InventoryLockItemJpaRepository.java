package org.tripsphere.inventory.adapter.outbound.persistence;

import java.util.List;
import org.springframework.data.jpa.repository.JpaRepository;
import org.tripsphere.inventory.adapter.outbound.persistence.entity.InventoryLockItemEntity;

public interface InventoryLockItemJpaRepository extends JpaRepository<InventoryLockItemEntity, String> {

    List<InventoryLockItemEntity> findByLockId(String lockId);
}
