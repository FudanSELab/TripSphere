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
public class ReleaseLockUseCase {

    private final DailyInventoryRepository dailyInventoryRepository;
    private final InventoryLockRepository inventoryLockRepository;
    private final InventoryCachePort cachePort;
    private final LockExpiryPort lockExpiryPort;

    @Transactional
    public InventoryLock execute(String lockId, String reason) {
        log.debug("Releasing lock: {}, reason: {}", lockId, reason);

        InventoryLock lock = inventoryLockRepository
                .findByLockId(lockId)
                .orElseThrow(() -> new NotFoundException("InventoryLock", lockId));

        if (lock.isAlreadyReleased()) {
            log.info("Lock {} already {}", lockId, lock.getStatus());
            return lock;
        }

        lock.release();

        List<DailyInventory> updatedInventories = new ArrayList<>();
        for (InventoryLockItem item : lock.getItems()) {
            DailyInventory inventory = dailyInventoryRepository
                    .findBySkuIdAndDateForUpdate(item.getSkuId(), item.getInvDate())
                    .orElseThrow(
                            () -> new NotFoundException("DailyInventory", item.getSkuId() + "/" + item.getInvDate()));
            inventory.release(item.getQuantity());
            updatedInventories.add(inventory);
        }

        dailyInventoryRepository.saveAll(updatedInventories);
        lock = inventoryLockRepository.save(lock);

        updatedInventories.forEach(cachePort::cacheDailyInventory);
        lockExpiryPort.removeLockExpiry(lockId);

        log.info("Lock released: {}, reason: {}", lockId, reason);
        return lock;
    }
}
