package org.tripsphere.inventory.application.service.command;

import com.github.f4b6a3.uuid.UuidCreator;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.tripsphere.inventory.application.dto.SetDailyInventoryCommand;
import org.tripsphere.inventory.application.port.DailyInventoryRepository;
import org.tripsphere.inventory.application.port.InventoryCachePort;
import org.tripsphere.inventory.domain.model.DailyInventory;

@Slf4j
@Service
@RequiredArgsConstructor
public class SetDailyInventoryUseCase {

    private final DailyInventoryRepository dailyInventoryRepository;
    private final InventoryCachePort cachePort;

    @Transactional
    public DailyInventory execute(SetDailyInventoryCommand command) {
        log.debug(
                "Setting daily inventory: sku={}, date={}, total={}",
                command.skuId(),
                command.date(),
                command.totalQuantity());

        DailyInventory inventory = dailyInventoryRepository
                .findBySkuIdAndDate(command.skuId(), command.date())
                .orElse(null);

        if (inventory == null) {
            String id = UuidCreator.getTimeOrderedEpoch().toString();
            inventory = DailyInventory.create(
                    id, command.skuId(), command.date(), command.totalQuantity(), command.price());
        } else {
            inventory.updateTotal(command.totalQuantity());
            inventory.updatePrice(command.price());
        }

        inventory = dailyInventoryRepository.save(inventory);
        cachePort.cacheDailyInventory(inventory);

        log.info(
                "Set daily inventory: sku={}, date={}, total={}, available={}",
                command.skuId(),
                command.date(),
                inventory.getTotalQty(),
                inventory.getAvailableQty());
        return inventory;
    }
}
