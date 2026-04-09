package org.tripsphere.order.infrastructure.adapter.outbound.cache;

import java.time.Duration;
import java.util.Optional;
import java.util.Set;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Component;
import org.tripsphere.order.application.port.OrderCachePort;
import org.tripsphere.order.infrastructure.config.OrderProperties;

@Slf4j
@Component
@RequiredArgsConstructor
public class RedisOrderCacheAdapter implements OrderCachePort {

    private final StringRedisTemplate redisTemplate;
    private final OrderProperties properties;

    private static final String ORDER_EXPIRE_KEY = "order:expire";
    private static final String ORDER_DEDUP_KEY_PREFIX = "order:dedup:";
    private static final String IDEMPOTENCY_KEY_PREFIX = "order:idempotency:";

    @Override
    public boolean tryAcquireDedup(String userId, String fingerprint) {
        try {
            String dedupKey = ORDER_DEDUP_KEY_PREFIX + userId + ":" + Integer.toHexString(fingerprint.hashCode());
            Duration dedupWindow = Duration.ofSeconds(properties.dedupWindowSeconds());
            Boolean isNew = redisTemplate.opsForValue().setIfAbsent(dedupKey, "1", dedupWindow);
            return Boolean.TRUE.equals(isNew);
        } catch (Exception e) {
            log.warn("Redis dedup check failed, proceeding without dedup: {}", e.getMessage());
            return true;
        }
    }

    @Override
    public void addOrderExpiry(String orderId, long expireTimestamp) {
        try {
            redisTemplate.opsForZSet().add(ORDER_EXPIRE_KEY, orderId, expireTimestamp);
        } catch (Exception e) {
            log.warn("Failed to add order expiry to Redis: {}", e.getMessage());
        }
    }

    @Override
    public void removeOrderExpiry(String orderId) {
        try {
            redisTemplate.opsForZSet().remove(ORDER_EXPIRE_KEY, orderId);
        } catch (Exception e) {
            log.warn("Failed to remove order expiry from Redis: {}", e.getMessage());
        }
    }

    @Override
    public Set<String> getExpiredOrderIds(long now, int batchSize) {
        return redisTemplate.opsForZSet().rangeByScore(ORDER_EXPIRE_KEY, 0, now, 0, batchSize);
    }

    @Override
    public Optional<String> getIdempotentOrderId(String requestId) {
        try {
            String orderId = redisTemplate.opsForValue().get(IDEMPOTENCY_KEY_PREFIX + requestId);
            return Optional.ofNullable(orderId);
        } catch (Exception e) {
            log.warn("Redis idempotency check failed, proceeding without idempotency guard: {}", e.getMessage());
            return Optional.empty();
        }
    }

    @Override
    public void saveIdempotentOrderId(String requestId, String orderId, long ttlSeconds) {
        try {
            redisTemplate
                    .opsForValue()
                    .set(IDEMPOTENCY_KEY_PREFIX + requestId, orderId, Duration.ofSeconds(ttlSeconds));
        } catch (Exception e) {
            log.warn("Failed to save idempotency record for request_id={}: {}", requestId, e.getMessage());
        }
    }
}
