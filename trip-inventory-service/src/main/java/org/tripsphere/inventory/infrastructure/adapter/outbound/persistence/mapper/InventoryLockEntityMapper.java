package org.tripsphere.inventory.infrastructure.adapter.outbound.persistence.mapper;

import java.util.ArrayList;
import java.util.List;
import org.mapstruct.Mapper;
import org.mapstruct.MappingConstants;
import org.mapstruct.NullValueCheckStrategy;
import org.tripsphere.inventory.domain.model.InventoryLock;
import org.tripsphere.inventory.domain.model.InventoryLockItem;
import org.tripsphere.inventory.domain.model.LockStatus;
import org.tripsphere.inventory.infrastructure.adapter.outbound.persistence.entity.InventoryLockEntity;
import org.tripsphere.inventory.infrastructure.adapter.outbound.persistence.entity.InventoryLockItemEntity;

@Mapper(componentModel = MappingConstants.ComponentModel.SPRING, nullValueCheckStrategy = NullValueCheckStrategy.ALWAYS)
public interface InventoryLockEntityMapper {

    InventoryLockEntity toEntity(InventoryLock domain);

    InventoryLockItemEntity toItemEntity(InventoryLockItem domain);

    List<InventoryLockItemEntity> toItemEntities(List<InventoryLockItem> items);

    InventoryLockItem toItemDomain(InventoryLockItemEntity entity);

    List<InventoryLockItem> toItemDomains(List<InventoryLockItemEntity> entities);

    default InventoryLock toDomain(InventoryLockEntity entity, List<InventoryLockItem> items) {
        if (entity == null) return null;
        return InventoryLock.builder()
                .lockId(entity.getLockId())
                .orderId(entity.getOrderId())
                .status(LockStatus.valueOf(entity.getStatus()))
                .createdAt(entity.getCreatedAt())
                .expireAt(entity.getExpireAt())
                .items(items != null ? new ArrayList<>(items) : new ArrayList<>())
                .build();
    }

    default String mapLockStatus(LockStatus status) {
        return status != null ? status.name() : null;
    }
}
