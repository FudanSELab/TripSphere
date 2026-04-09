package org.tripsphere.inventory.application.service.query;

import java.time.LocalDate;
import java.util.List;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.tripsphere.inventory.application.port.DailyInventoryRepository;
import org.tripsphere.inventory.application.port.InventoryCachePort;
import org.tripsphere.inventory.domain.model.DailyInventory;

@Slf4j
@Service
@RequiredArgsConstructor
public class QueryInventoryCalendarUseCase {

    private final DailyInventoryRepository dailyInventoryRepository;
    private final InventoryCachePort cachePort;

    public List<DailyInventory> execute(String skuId, LocalDate startDate, LocalDate endDate) {
        log.debug("Querying inventory calendar: sku={}, from={}, to={}", skuId, startDate, endDate);

        List<DailyInventory> inventories = dailyInventoryRepository.findBySkuIdAndDateRange(skuId, startDate, endDate);

        inventories.forEach(cachePort::cacheDailyInventory);

        return inventories;
    }
}
