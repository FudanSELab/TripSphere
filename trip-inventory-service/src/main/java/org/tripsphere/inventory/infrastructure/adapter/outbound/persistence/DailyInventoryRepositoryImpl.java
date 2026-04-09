package org.tripsphere.inventory.infrastructure.adapter.outbound.persistence;

import java.time.LocalDate;
import java.util.List;
import java.util.Optional;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Repository;
import org.tripsphere.inventory.application.port.DailyInventoryRepository;
import org.tripsphere.inventory.domain.model.DailyInventory;
import org.tripsphere.inventory.infrastructure.adapter.outbound.persistence.entity.DailyInventoryEntity;
import org.tripsphere.inventory.infrastructure.adapter.outbound.persistence.mapper.DailyInventoryEntityMapper;

@Repository
@RequiredArgsConstructor
public class DailyInventoryRepositoryImpl implements DailyInventoryRepository {

    private final DailyInventoryJpaRepository jpaRepository;
    private final DailyInventoryEntityMapper mapper;

    @Override
    public DailyInventory save(DailyInventory inventory) {
        DailyInventoryEntity entity = mapper.toEntity(inventory);
        DailyInventoryEntity saved = jpaRepository.save(entity);
        return mapper.toDomain(saved);
    }

    @Override
    public List<DailyInventory> saveAll(List<DailyInventory> inventories) {
        List<DailyInventoryEntity> entities =
                inventories.stream().map(mapper::toEntity).toList();
        List<DailyInventoryEntity> saved = jpaRepository.saveAll(entities);
        return mapper.toDomains(saved);
    }

    @Override
    public Optional<DailyInventory> findBySkuIdAndDate(String skuId, LocalDate date) {
        return jpaRepository.findBySkuIdAndInvDate(skuId, date).map(mapper::toDomain);
    }

    @Override
    public Optional<DailyInventory> findBySkuIdAndDateForUpdate(String skuId, LocalDate date) {
        return jpaRepository.findBySkuIdAndInvDateForUpdate(skuId, date).map(mapper::toDomain);
    }

    @Override
    public List<DailyInventory> findBySkuIdAndDateRange(String skuId, LocalDate startDate, LocalDate endDate) {
        return mapper.toDomains(jpaRepository.findBySkuIdAndInvDateBetweenOrderByInvDateAsc(skuId, startDate, endDate));
    }
}
