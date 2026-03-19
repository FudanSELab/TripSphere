package org.tripsphere.inventory.adapter.inbound.scheduler;

import java.time.Instant;
import java.util.Set;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;
import org.tripsphere.inventory.application.port.LockExpiryPort;
import org.tripsphere.inventory.application.service.command.ReleaseLockUseCase;
import org.tripsphere.inventory.config.InventoryProperties;

@Slf4j
@Component
@RequiredArgsConstructor
public class LockExpiryScheduler {

    private final LockExpiryPort lockExpiryPort;
    private final ReleaseLockUseCase releaseLockUseCase;
    private final InventoryProperties properties;

    @Scheduled(fixedDelay = 30000)
    public void releaseExpiredLocks() {
        long now = Instant.now().getEpochSecond();
        Set<String> expiredLockIds = lockExpiryPort.getExpiredLockIds(now, properties.lockExpiryBatchSize());

        if (expiredLockIds == null || expiredLockIds.isEmpty()) {
            return;
        }

        log.info("Found {} expired locks to release", expiredLockIds.size());

        for (String lockId : expiredLockIds) {
            try {
                releaseLockUseCase.execute(lockId, "Lock expired - auto released");
                log.info("Auto-released expired lock: {}", lockId);
            } catch (Exception e) {
                log.error("Failed to release expired lock: {}", lockId, e);
                lockExpiryPort.removeLockExpiry(lockId);
            }
        }
    }
}
