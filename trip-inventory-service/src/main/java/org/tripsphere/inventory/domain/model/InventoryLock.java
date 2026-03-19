package org.tripsphere.inventory.domain.model;

import java.time.Instant;
import java.time.LocalDate;
import java.util.ArrayList;
import java.util.List;
import lombok.Builder;
import lombok.Getter;
import org.tripsphere.inventory.domain.exception.InvalidLockStateException;

@Getter
@Builder
public class InventoryLock {
    private String lockId;
    private String orderId;
    private LockStatus status;
    private long createdAt;
    private long expireAt;

    @Builder.Default
    private List<InventoryLockItem> items = new ArrayList<>();

    public static InventoryLock create(String lockId, String orderId, int lockTimeoutSeconds) {
        long now = Instant.now().getEpochSecond();
        return InventoryLock.builder()
                .lockId(lockId)
                .orderId(orderId)
                .status(LockStatus.LOCKED)
                .createdAt(now)
                .expireAt(now + lockTimeoutSeconds)
                .build();
    }

    public void addItem(String itemId, String skuId, LocalDate invDate, int quantity) {
        InventoryLockItem item = InventoryLockItem.create(itemId, this.lockId, skuId, invDate, quantity);
        this.items.add(item);
    }

    public void confirm() {
        if (this.status == LockStatus.CONFIRMED) {
            return;
        }
        if (this.status != LockStatus.LOCKED) {
            throw new InvalidLockStateException(lockId, status.name(), "confirm");
        }
        this.status = LockStatus.CONFIRMED;
    }

    public void release() {
        if (this.status == LockStatus.RELEASED || this.status == LockStatus.EXPIRED) {
            return;
        }
        if (this.status != LockStatus.LOCKED) {
            throw new InvalidLockStateException(lockId, status.name(), "release");
        }
        this.status = LockStatus.RELEASED;
    }

    public boolean isAlreadyConfirmed() {
        return this.status == LockStatus.CONFIRMED;
    }

    public boolean isAlreadyReleased() {
        return this.status == LockStatus.RELEASED || this.status == LockStatus.EXPIRED;
    }
}
