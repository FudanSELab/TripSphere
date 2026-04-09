package org.tripsphere.inventory.application.port;

import java.time.LocalDate;
import java.util.Optional;
import org.tripsphere.inventory.domain.model.DailyInventory;

public interface InventoryCachePort {

    void cacheDailyInventory(DailyInventory inventory);

    Optional<DailyInventory> getCachedInventory(String skuId, LocalDate date);

    boolean tryAcquireCacheMutex(String skuId, LocalDate date);
}
