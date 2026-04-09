package org.tripsphere.order.application.port;

import java.util.Optional;
import java.util.Set;

public interface OrderCachePort {

    boolean tryAcquireDedup(String userId, String fingerprint);

    void addOrderExpiry(String orderId, long expireTimestamp);

    void removeOrderExpiry(String orderId);

    Set<String> getExpiredOrderIds(long now, int batchSize);

    Optional<String> getIdempotentOrderId(String requestId);

    void saveIdempotentOrderId(String requestId, String orderId, long ttlSeconds);
}
