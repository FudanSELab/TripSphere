package org.tripsphere.inventory.application.service.query;

import java.time.LocalDate;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.tripsphere.inventory.application.exception.NotFoundException;
import org.tripsphere.inventory.application.port.InventoryCachePort;
import org.tripsphere.inventory.domain.model.DailyInventory;
import org.tripsphere.inventory.domain.repository.DailyInventoryRepository;

@Slf4j
@Service
@RequiredArgsConstructor
public class GetDailyInventoryUseCase {

    private final DailyInventoryRepository dailyInventoryRepository;
    private final InventoryCachePort cachePort;

    public DailyInventory execute(String skuId, LocalDate date) {
        log.debug("Getting daily inventory: sku={}, date={}", skuId, date);

        return cachePort.getCachedInventory(skuId, date).orElseGet(() -> {
            boolean shouldRebuild = cachePort.tryAcquireCacheMutex(skuId, date);
            DailyInventory inventory = dailyInventoryRepository
                    .findBySkuIdAndDate(skuId, date)
                    .orElseThrow(
                            () -> new NotFoundException("DailyInventory not found: skuId=" + skuId + ", date=" + date));
            if (shouldRebuild) {
                cachePort.cacheDailyInventory(inventory);
            }
            return inventory;
        });
    }
}
