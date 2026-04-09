package org.tripsphere.inventory.infrastructure.adapter.outbound.persistence.mapper;

import java.util.List;
import org.mapstruct.Mapper;
import org.mapstruct.Mapping;
import org.mapstruct.MappingConstants;
import org.mapstruct.NullValueCheckStrategy;
import org.tripsphere.inventory.domain.model.DailyInventory;
import org.tripsphere.inventory.domain.model.Money;
import org.tripsphere.inventory.infrastructure.adapter.outbound.persistence.entity.DailyInventoryEntity;

@Mapper(componentModel = MappingConstants.ComponentModel.SPRING, nullValueCheckStrategy = NullValueCheckStrategy.ALWAYS)
public interface DailyInventoryEntityMapper {

    @Mapping(target = "priceCurrency", source = "price.currency")
    @Mapping(target = "priceUnits", source = "price.units")
    @Mapping(target = "priceNanos", source = "price.nanos")
    DailyInventoryEntity toEntity(DailyInventory domain);

    @Mapping(target = "price", expression = "java(toMoney(entity))")
    DailyInventory toDomain(DailyInventoryEntity entity);

    List<DailyInventory> toDomains(List<DailyInventoryEntity> entities);

    default Money toMoney(DailyInventoryEntity entity) {
        if (entity == null) return null;
        return new Money(entity.getPriceCurrency(), entity.getPriceUnits(), entity.getPriceNanos());
    }
}
