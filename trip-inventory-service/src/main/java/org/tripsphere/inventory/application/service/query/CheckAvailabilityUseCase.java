package org.tripsphere.inventory.application.service.query;

import java.time.LocalDate;
import java.util.Optional;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.tripsphere.inventory.application.dto.CheckAvailabilityResult;
import org.tripsphere.inventory.application.port.InventoryCachePort;
import org.tripsphere.inventory.domain.model.DailyInventory;
import org.tripsphere.inventory.domain.model.Money;
import org.tripsphere.inventory.domain.repository.DailyInventoryRepository;

@Slf4j
@Service
@RequiredArgsConstructor
public class CheckAvailabilityUseCase {

    private final DailyInventoryRepository dailyInventoryRepository;
    private final InventoryCachePort cachePort;

    public CheckAvailabilityResult execute(String skuId, LocalDate date, int quantity) {
        log.debug("Checking availability: sku={}, date={}, qty={}", skuId, date, quantity);

        Optional<DailyInventory> cached = cachePort.getCachedInventory(skuId, date);
        if (cached.isPresent()) {
            DailyInventory inv = cached.get();
            return new CheckAvailabilityResult(
                    inv.getAvailableQty() >= quantity, inv.getAvailableQty(), inv.getPrice());
        }

        DailyInventory inventory =
                dailyInventoryRepository.findBySkuIdAndDate(skuId, date).orElse(null);

        if (inventory == null) {
            return new CheckAvailabilityResult(false, 0, Money.cny(0, 0));
        }

        cachePort.cacheDailyInventory(inventory);
        return new CheckAvailabilityResult(
                inventory.getAvailableQty() >= quantity, inventory.getAvailableQty(), inventory.getPrice());
    }
}
