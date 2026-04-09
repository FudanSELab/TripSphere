package org.tripsphere.inventory.application.service.command;

import java.util.ArrayList;
import java.util.List;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.tripsphere.inventory.application.exception.NotFoundException;
import org.tripsphere.inventory.application.port.DailyInventoryRepository;
import org.tripsphere.inventory.application.port.InventoryCachePort;
import org.tripsphere.inventory.application.port.InventoryLockRepository;
import org.tripsphere.inventory.application.port.LockExpiryPort;
import org.tripsphere.inventory.domain.model.DailyInventory;
import org.tripsphere.inventory.domain.model.InventoryLock;
import org.tripsphere.inventory.domain.model.InventoryLockItem;

@Slf4j
@Service
@RequiredArgsConstructor
public class ConfirmLockUseCase {

    private final DailyInventoryRepository dailyInventoryRepository;
    private final InventoryLockRepository inventoryLockRepository;
    private final InventoryCachePort cachePort;
    private final LockExpiryPort lockExpiryPort;

    @Transactional
    public InventoryLock execute(String lockId) {
        log.debug("Confirming lock: {}", lockId);

        InventoryLock lock = inventoryLockRepository
                .findByLockId(lockId)
                .orElseThrow(() -> new NotFoundException("InventoryLock", lockId));

        if (lock.isAlreadyConfirmed()) {
            log.info("Lock {} already confirmed", lockId);
            return lock;
        }

        lock.confirm();

        List<DailyInventory> updatedInventories = new ArrayList<>();
        for (InventoryLockItem item : lock.getItems()) {
            DailyInventory inventory = dailyInventoryRepository
                    .findBySkuIdAndDateForUpdate(item.getSkuId(), item.getInvDate())
                    .orElseThrow(
                            () -> new NotFoundException("DailyInventory", item.getSkuId() + "/" + item.getInvDate()));
            inventory.confirmSold(item.getQuantity());
            updatedInventories.add(inventory);
        }

        dailyInventoryRepository.saveAll(updatedInventories);
        lock = inventoryLockRepository.save(lock);

        updatedInventories.forEach(cachePort::cacheDailyInventory);
        lockExpiryPort.removeLockExpiry(lockId);

        log.info("Lock confirmed: {}", lockId);
        return lock;
    }
}
