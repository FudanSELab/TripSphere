package org.tripsphere.inventory.application.port;

import java.util.Set;

public interface LockExpiryPort {

    void addLockExpiry(String lockId, long expireTimestamp);

    void removeLockExpiry(String lockId);

    Set<String> getExpiredLockIds(long now, int batchSize);
}
