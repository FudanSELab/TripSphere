package org.tripsphere.inventory.adapter.outbound.cache;

import java.time.LocalDate;
import java.util.HashMap;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.concurrent.TimeUnit;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Component;
import org.tripsphere.inventory.application.port.InventoryCachePort;
import org.tripsphere.inventory.application.port.LockExpiryPort;
import org.tripsphere.inventory.domain.model.DailyInventory;
import org.tripsphere.inventory.domain.model.Money;

@Slf4j
@Component
@RequiredArgsConstructor
public class RedisInventoryCacheAdapter implements InventoryCachePort, LockExpiryPort {

    private final StringRedisTemplate redisTemplate;

    private static final String INV_KEY_PREFIX = "inv:";
    private static final String LOCK_EXPIRY_KEY = "inv:lock:expiry";
    private static final String MUTEX_KEY_PREFIX = "inv:mutex:";

    private String buildKey(String skuId, LocalDate date) {
        return INV_KEY_PREFIX + skuId + ":" + date.toString();
    }

    // ── InventoryCachePort ────────────────────────────────────

    @Override
    public void cacheDailyInventory(DailyInventory inventory) {
        try {
            String key = buildKey(inventory.getSkuId(), inventory.getInvDate());
            Map<String, String> hash = new HashMap<>();
            hash.put("total", String.valueOf(inventory.getTotalQty()));
            hash.put("available", String.valueOf(inventory.getAvailableQty()));
            hash.put("locked", String.valueOf(inventory.getLockedQty()));
            hash.put("sold", String.valueOf(inventory.getSoldQty()));
            hash.put("price_units", String.valueOf(inventory.getPrice().units()));
            hash.put("price_nanos", String.valueOf(inventory.getPrice().nanos()));
            hash.put("price_ccy", inventory.getPrice().currency());
            redisTemplate.opsForHash().putAll(key, hash);
            redisTemplate.expire(key, 7, TimeUnit.DAYS);
        } catch (Exception e) {
            log.warn(
                    "Failed to cache inventory for sku={}, date={}: {}",
                    inventory.getSkuId(),
                    inventory.getInvDate(),
                    e.getMessage());
        }
    }

    @Override
    public Optional<DailyInventory> getCachedInventory(String skuId, LocalDate date) {
        String key = buildKey(skuId, date);
        Map<Object, Object> entries = redisTemplate.opsForHash().entries(key);
        if (entries.isEmpty()) {
            return Optional.empty();
        }
        Map<String, String> cached = new HashMap<>();
        entries.forEach((k, v) -> cached.put(k.toString(), v.toString()));

        DailyInventory inventory = DailyInventory.builder()
                .skuId(skuId)
                .invDate(date)
                .totalQty(Integer.parseInt(cached.getOrDefault("total", "0")))
                .availableQty(Integer.parseInt(cached.getOrDefault("available", "0")))
                .lockedQty(Integer.parseInt(cached.getOrDefault("locked", "0")))
                .soldQty(Integer.parseInt(cached.getOrDefault("sold", "0")))
                .price(new Money(
                        cached.getOrDefault("price_ccy", "CNY"),
                        Long.parseLong(cached.getOrDefault("price_units", "0")),
                        Integer.parseInt(cached.getOrDefault("price_nanos", "0"))))
                .build();
        return Optional.of(inventory);
    }

    @Override
    public boolean tryAcquireCacheMutex(String skuId, LocalDate date) {
        String mutexKey = MUTEX_KEY_PREFIX + skuId + ":" + date.toString();
        Boolean acquired = redisTemplate.opsForValue().setIfAbsent(mutexKey, "1", 5, TimeUnit.SECONDS);
        return Boolean.TRUE.equals(acquired);
    }

    // ── LockExpiryPort ────────────────────────────────────────

    @Override
    public void addLockExpiry(String lockId, long expireTimestamp) {
        try {
            redisTemplate.opsForZSet().add(LOCK_EXPIRY_KEY, lockId, expireTimestamp);
        } catch (Exception e) {
            log.warn("Failed to add lock expiry for lockId={}: {}", lockId, e.getMessage());
        }
    }

    @Override
    public void removeLockExpiry(String lockId) {
        try {
            redisTemplate.opsForZSet().remove(LOCK_EXPIRY_KEY, lockId);
        } catch (Exception e) {
            log.warn("Failed to remove lock expiry for lockId={}: {}", lockId, e.getMessage());
        }
    }

    @Override
    public Set<String> getExpiredLockIds(long now, int batchSize) {
        return redisTemplate.opsForZSet().rangeByScore(LOCK_EXPIRY_KEY, 0, now, 0, batchSize);
    }
}
