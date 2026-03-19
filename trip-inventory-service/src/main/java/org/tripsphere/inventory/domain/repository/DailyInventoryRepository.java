package org.tripsphere.inventory.domain.repository;

import java.time.LocalDate;
import java.util.List;
import java.util.Optional;
import org.tripsphere.inventory.domain.model.DailyInventory;

public interface DailyInventoryRepository {

    DailyInventory save(DailyInventory inventory);

    List<DailyInventory> saveAll(List<DailyInventory> inventories);

    Optional<DailyInventory> findBySkuIdAndDate(String skuId, LocalDate date);

    Optional<DailyInventory> findBySkuIdAndDateForUpdate(String skuId, LocalDate date);

    List<DailyInventory> findBySkuIdAndDateRange(String skuId, LocalDate startDate, LocalDate endDate);
}
