package org.tripsphere.inventory.adapter.inbound.grpc.mapper;

import java.util.List;
import org.mapstruct.*;
import org.tripsphere.inventory.domain.model.DailyInventory;

@Mapper(
        componentModel = MappingConstants.ComponentModel.SPRING,
        collectionMappingStrategy = CollectionMappingStrategy.ADDER_PREFERRED,
        nullValueCheckStrategy = NullValueCheckStrategy.ALWAYS,
        uses = {DateProtoMapper.class, MoneyProtoMapper.class})
public interface DailyInventoryProtoMapper {

    @Mapping(source = "invDate", target = "date")
    @Mapping(source = "totalQty", target = "totalQuantity")
    @Mapping(source = "availableQty", target = "availableQuantity")
    @Mapping(source = "lockedQty", target = "lockedQuantity")
    @Mapping(source = "soldQty", target = "soldQuantity")
    org.tripsphere.inventory.v1.DailyInventory toProto(DailyInventory domain);

    List<org.tripsphere.inventory.v1.DailyInventory> toProtos(List<DailyInventory> domains);
}
