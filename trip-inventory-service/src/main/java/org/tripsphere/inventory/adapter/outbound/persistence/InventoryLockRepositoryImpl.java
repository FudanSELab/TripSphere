package org.tripsphere.inventory.adapter.outbound.persistence;

import java.util.List;
import java.util.Optional;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Repository;
import org.tripsphere.inventory.adapter.outbound.persistence.entity.InventoryLockEntity;
import org.tripsphere.inventory.adapter.outbound.persistence.entity.InventoryLockItemEntity;
import org.tripsphere.inventory.adapter.outbound.persistence.mapper.InventoryLockEntityMapper;
import org.tripsphere.inventory.domain.model.InventoryLock;
import org.tripsphere.inventory.domain.model.InventoryLockItem;
import org.tripsphere.inventory.domain.repository.InventoryLockRepository;

@Repository
@RequiredArgsConstructor
public class InventoryLockRepositoryImpl implements InventoryLockRepository {

    private final InventoryLockJpaRepository lockJpaRepository;
    private final InventoryLockItemJpaRepository lockItemJpaRepository;
    private final InventoryLockEntityMapper mapper;

    @Override
    public InventoryLock save(InventoryLock lock) {
        InventoryLockEntity lockEntity = mapper.toEntity(lock);
        lockEntity = lockJpaRepository.save(lockEntity);

        List<InventoryLockItemEntity> itemEntities = mapper.toItemEntities(lock.getItems());
        lockItemJpaRepository.saveAll(itemEntities);

        List<InventoryLockItem> items = mapper.toItemDomains(lockItemJpaRepository.findByLockId(lock.getLockId()));
        return mapper.toDomain(lockEntity, items);
    }

    @Override
    public Optional<InventoryLock> findByLockId(String lockId) {
        return lockJpaRepository.findByLockId(lockId).map(this::assembleLock);
    }

    @Override
    public Optional<InventoryLock> findByOrderId(String orderId) {
        return lockJpaRepository.findByOrderId(orderId).map(this::assembleLock);
    }

    private InventoryLock assembleLock(InventoryLockEntity entity) {
        List<InventoryLockItemEntity> itemEntities = lockItemJpaRepository.findByLockId(entity.getLockId());
        List<InventoryLockItem> items = mapper.toItemDomains(itemEntities);
        return mapper.toDomain(entity, items);
    }
}
