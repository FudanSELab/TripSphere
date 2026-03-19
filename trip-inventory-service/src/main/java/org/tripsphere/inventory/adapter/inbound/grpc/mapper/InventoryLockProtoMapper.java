package org.tripsphere.inventory.adapter.inbound.grpc.mapper;

import com.google.protobuf.Timestamp;
import java.util.List;
import org.mapstruct.*;
import org.tripsphere.inventory.domain.model.InventoryLock;
import org.tripsphere.inventory.domain.model.InventoryLockItem;
import org.tripsphere.inventory.domain.model.LockStatus;

@Mapper(
        componentModel = MappingConstants.ComponentModel.SPRING,
        collectionMappingStrategy = CollectionMappingStrategy.ADDER_PREFERRED,
        nullValueCheckStrategy = NullValueCheckStrategy.ALWAYS,
        uses = {DateProtoMapper.class})
public interface InventoryLockProtoMapper {

    org.tripsphere.inventory.v1.InventoryLock toProto(InventoryLock domain);

    @Mapping(source = "invDate", target = "date")
    org.tripsphere.inventory.v1.LockItem toItemProto(InventoryLockItem item);

    List<org.tripsphere.inventory.v1.LockItem> toItemProtos(List<InventoryLockItem> items);

    @ValueMapping(source = "LOCKED", target = "LOCK_STATUS_LOCKED")
    @ValueMapping(source = "CONFIRMED", target = "LOCK_STATUS_CONFIRMED")
    @ValueMapping(source = "RELEASED", target = "LOCK_STATUS_RELEASED")
    @ValueMapping(source = "EXPIRED", target = "LOCK_STATUS_EXPIRED")
    org.tripsphere.inventory.v1.LockStatus mapStatus(LockStatus status);

    default Timestamp mapToTimestamp(long epoch) {
        return Timestamp.newBuilder().setSeconds(epoch).build();
    }
}
