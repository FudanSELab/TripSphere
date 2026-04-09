package org.tripsphere.inventory.application.service.command;

import com.github.f4b6a3.uuid.UuidCreator;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.tripsphere.inventory.application.dto.LockInventoryCommand;
import org.tripsphere.inventory.application.exception.InsufficientInventoryException;
import org.tripsphere.inventory.application.exception.InvalidArgumentException;
import org.tripsphere.inventory.application.exception.NotFoundException;
import org.tripsphere.inventory.application.port.DailyInventoryRepository;
import org.tripsphere.inventory.application.port.InventoryCachePort;
import org.tripsphere.inventory.application.port.InventoryConfigPort;
import org.tripsphere.inventory.application.port.InventoryLockRepository;
import org.tripsphere.inventory.application.port.LockExpiryPort;
import org.tripsphere.inventory.domain.model.DailyInventory;
import org.tripsphere.inventory.domain.model.InventoryLock;
import org.tripsphere.inventory.domain.model.LockStatus;

@Slf4j
@Service
@RequiredArgsConstructor
public class LockInventoryUseCase {

    private final DailyInventoryRepository dailyInventoryRepository;
    private final InventoryLockRepository inventoryLockRepository;
    private final InventoryCachePort cachePort;
    private final LockExpiryPort lockExpiryPort;
    private final InventoryConfigPort configPort;

    @Transactional
    public InventoryLock execute(LockInventoryCommand command) {
        log.debug(
                "Locking inventory for order: {}, items: {}",
                command.orderId(),
                command.items().size());

        int lockTimeout = command.lockTimeoutSeconds() <= 0
                ? configPort.defaultLockTimeoutSeconds()
                : command.lockTimeoutSeconds();

        Optional<InventoryLock> existingLock = inventoryLockRepository.findByOrderId(command.orderId());
        if (existingLock.isPresent()) {
            InventoryLock existing = existingLock.get();
            if (existing.getStatus() == LockStatus.LOCKED) {
                log.info("Lock already exists for order {}, lockId={}", command.orderId(), existing.getLockId());
                return existing;
            }
            throw new InvalidArgumentException(
                    "Order " + command.orderId() + " already has a lock in status " + existing.getStatus());
        }

        String lockId = UuidCreator.getTimeOrderedEpoch().toString();
        InventoryLock lock = InventoryLock.create(lockId, command.orderId(), lockTimeout);
        List<DailyInventory> lockedInventories = new ArrayList<>();

        for (LockInventoryCommand.LockItemCommand item : command.items()) {
            DailyInventory inventory = dailyInventoryRepository
                    .findBySkuIdAndDateForUpdate(item.skuId(), item.date())
                    .orElseThrow(() -> new NotFoundException("DailyInventory", item.skuId() + "/" + item.date()));

            if (inventory.getAvailableQty() < item.quantity()) {
                throw new InsufficientInventoryException(
                        item.skuId(), item.date().toString(), item.quantity(), inventory.getAvailableQty());
            }

            inventory.lock(item.quantity());
            lockedInventories.add(inventory);

            String itemId = UuidCreator.getTimeOrderedEpoch().toString();
            lock.addItem(itemId, item.skuId(), item.date(), item.quantity());
        }

        dailyInventoryRepository.saveAll(lockedInventories);
        lock = inventoryLockRepository.save(lock);

        lockedInventories.forEach(cachePort::cacheDailyInventory);
        lockExpiryPort.addLockExpiry(lock.getLockId(), lock.getExpireAt());

        log.info(
                "Inventory locked: lockId={}, orderId={}, expireAt={}",
                lock.getLockId(),
                command.orderId(),
                lock.getExpireAt());
        return lock;
    }
}
