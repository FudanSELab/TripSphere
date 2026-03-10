package org.tripsphere.inventory.service.impl;

import com.github.f4b6a3.uuid.UuidCreator;
import java.time.Instant;
import java.time.LocalDate;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.tripsphere.inventory.exception.InsufficientInventoryException;
import org.tripsphere.inventory.exception.InvalidArgumentException;
import org.tripsphere.inventory.exception.NotFoundException;
import org.tripsphere.inventory.infra.redis.RedisInventoryClient;
import org.tripsphere.inventory.mapper.InventoryMapper;
import org.tripsphere.inventory.model.DailyInventoryEntity;
import org.tripsphere.inventory.model.InventoryLockEntity;
import org.tripsphere.inventory.model.InventoryLockItemEntity;
import org.tripsphere.inventory.repository.DailyInventoryRepository;
import org.tripsphere.inventory.repository.InventoryLockItemRepository;
import org.tripsphere.inventory.repository.InventoryLockRepository;
import org.tripsphere.inventory.service.InventoryService;
import org.tripsphere.inventory.v1.DailyInventory;
import org.tripsphere.inventory.v1.InventoryLock;
import org.tripsphere.inventory.v1.LockItem;

/** MySQL is source of truth; Redis is read-only cache updated best-effort after commits. */
@Slf4j
@Service
@RequiredArgsConstructor
public class InventoryServiceImpl implements InventoryService {

    private final DailyInventoryRepository dailyInventoryRepository;
    private final InventoryLockRepository inventoryLockRepository;
    private final InventoryLockItemRepository inventoryLockItemRepository;
    private final RedisInventoryClient redisClient;
    private final InventoryMapper inventoryMapper = InventoryMapper.INSTANCE;

    private static final int DEFAULT_LOCK_TIMEOUT = 900;

    @Override
    @Transactional
    public DailyInventory setDailyInventory(
            String skuId,
            LocalDate date,
            int totalQuantity,
            String priceCurrency,
            long priceUnits,
            int priceNanos) {
        log.debug("Setting daily inventory: sku={}, date={}, total={}", skuId, date, totalQuantity);

        DailyInventoryEntity entity =
                dailyInventoryRepository.findBySkuIdAndInvDate(skuId, date).orElse(null);

        if (entity == null) {
            entity =
                    DailyInventoryEntity.builder()
                            .skuId(skuId)
                            .invDate(date)
                            .totalQty(totalQuantity)
                            .availableQty(totalQuantity)
                            .lockedQty(0)
                            .soldQty(0)
                            .priceCurrency(priceCurrency)
                            .priceUnits(priceUnits)
                            .priceNanos(priceNanos)
                            .updatedAt(Instant.now())
                            .build();
        } else {
            int newAvailable = totalQuantity - entity.getLockedQty() - entity.getSoldQty();
            if (newAvailable < 0) {
                throw new InvalidArgumentException(
                        "Cannot set total_quantity to "
                                + totalQuantity
                                + ": would result in negative available quantity");
            }
            entity.setTotalQty(totalQuantity);
            entity.setAvailableQty(newAvailable);
            entity.setPriceCurrency(priceCurrency);
            entity.setPriceUnits(priceUnits);
            entity.setPriceNanos(priceNanos);
        }

        entity = dailyInventoryRepository.save(entity);

        redisClient.cacheInventory(entity);

        log.info(
                "Set daily inventory: sku={}, date={}, total={}, available={}",
                skuId,
                date,
                entity.getTotalQty(),
                entity.getAvailableQty());
        return inventoryMapper.toProto(entity);
    }

    @Override
    @Transactional
    public List<DailyInventory> batchSetDailyInventory(List<SetDailyInventoryParams> params) {
        log.debug("Batch setting {} daily inventory records", params.size());
        List<DailyInventory> results = new ArrayList<>();
        for (SetDailyInventoryParams p : params) {
            results.add(
                    setDailyInventory(
                            p.skuId(),
                            p.date(),
                            p.totalQuantity(),
                            p.priceCurrency(),
                            p.priceUnits(),
                            p.priceNanos()));
        }
        return results;
    }

    @Override
    public DailyInventory getDailyInventory(String skuId, LocalDate date) {
        log.debug("Getting daily inventory: sku={}, date={}", skuId, date);

        Map<String, String> cached = redisClient.getCachedInventory(skuId, date);
        if (cached != null) {
            return buildDailyInventoryFromCache(skuId, date, cached);
        }

        boolean shouldRebuild = redisClient.tryAcquireCacheMutex(skuId, date);
        DailyInventoryEntity entity =
                dailyInventoryRepository
                        .findBySkuIdAndInvDate(skuId, date)
                        .orElseThrow(
                                () -> new NotFoundException("DailyInventory", skuId + "/" + date));
        if (shouldRebuild) {
            redisClient.cacheInventory(entity);
        }
        return inventoryMapper.toProto(entity);
    }

    @Override
    public List<DailyInventory> queryInventoryCalendar(
            String skuId, LocalDate startDate, LocalDate endDate) {
        log.debug("Querying inventory calendar: sku={}, from={}, to={}", skuId, startDate, endDate);

        List<DailyInventoryEntity> entities =
                dailyInventoryRepository.findBySkuIdAndInvDateBetweenOrderByInvDateAsc(
                        skuId, startDate, endDate);

        entities.forEach(redisClient::cacheInventory);

        return inventoryMapper.toProtoList(entities);
    }

    @Override
    public CheckAvailabilityResult checkAvailability(String skuId, LocalDate date, int quantity) {
        log.debug("Checking availability: sku={}, date={}, qty={}", skuId, date, quantity);

        Map<String, String> cached = redisClient.getCachedInventory(skuId, date);
        if (cached != null) {
            int available = Integer.parseInt(cached.getOrDefault("available", "0"));
            return new CheckAvailabilityResult(
                    available >= quantity,
                    available,
                    cached.getOrDefault("price_ccy", "CNY"),
                    Long.parseLong(cached.getOrDefault("price_units", "0")),
                    Integer.parseInt(cached.getOrDefault("price_nanos", "0")));
        }

        DailyInventoryEntity entity =
                dailyInventoryRepository.findBySkuIdAndInvDate(skuId, date).orElse(null);

        if (entity == null) {
            return new CheckAvailabilityResult(false, 0, "CNY", 0, 0);
        }

        redisClient.cacheInventory(entity);
        return new CheckAvailabilityResult(
                entity.getAvailableQty() >= quantity,
                entity.getAvailableQty(),
                entity.getPriceCurrency(),
                entity.getPriceUnits(),
                entity.getPriceNanos());
    }

    /** Idempotent: returns existing lock if already locked for this order. */
    @Override
    @Transactional
    public InventoryLock lockInventory(
            List<LockItem> items, String orderId, int lockTimeoutSeconds) {
        log.debug("Locking inventory for order: {}, items: {}", orderId, items.size());

        if (lockTimeoutSeconds <= 0) {
            lockTimeoutSeconds = DEFAULT_LOCK_TIMEOUT;
        }

        Optional<InventoryLockEntity> existingLock = inventoryLockRepository.findByOrderId(orderId);
        if (existingLock.isPresent()) {
            InventoryLockEntity existing = existingLock.get();
            if ("LOCKED".equals(existing.getStatus())) {
                log.info(
                        "Lock already exists for order {}, lockId={}",
                        orderId,
                        existing.getLockId());
                return inventoryMapper.toLockProto(existing);
            }
            throw new InvalidArgumentException(
                    "Order " + orderId + " already has a lock in status " + existing.getStatus());
        }

        List<String> skuIds = new ArrayList<>();
        List<LocalDate> dates = new ArrayList<>();
        List<Integer> quantities = new ArrayList<>();
        List<DailyInventoryEntity> lockedEntities = new ArrayList<>();

        for (LockItem item : items) {
            String skuId = item.getSkuId();
            LocalDate date = inventoryMapper.protoToLocalDate(item.getDate());
            int qty = item.getQuantity();

            skuIds.add(skuId);
            dates.add(date);
            quantities.add(qty);

            DailyInventoryEntity entity =
                    dailyInventoryRepository
                            .findBySkuIdAndInvDateForUpdate(skuId, date)
                            .orElseThrow(
                                    () ->
                                            new NotFoundException(
                                                    "DailyInventory", skuId + "/" + date));

            if (entity.getAvailableQty() < qty) {
                throw new InsufficientInventoryException(
                        skuId, date.toString(), qty, entity.getAvailableQty());
            }

            entity.setAvailableQty(entity.getAvailableQty() - qty);
            entity.setLockedQty(entity.getLockedQty() + qty);
            lockedEntities.add(entity);
        }

        dailyInventoryRepository.saveAll(lockedEntities);

        long now = Instant.now().getEpochSecond();
        long expireAt = now + lockTimeoutSeconds;
        String lockId = UuidCreator.getTimeOrderedEpoch().toString();

        InventoryLockEntity lockEntity =
                InventoryLockEntity.builder()
                        .lockId(lockId)
                        .orderId(orderId)
                        .status("LOCKED")
                        .createdAt(now)
                        .expireAt(expireAt)
                        .build();
        lockEntity = inventoryLockRepository.save(lockEntity);

        List<InventoryLockItemEntity> lockItems = new ArrayList<>();
        for (int i = 0; i < skuIds.size(); i++) {
            lockItems.add(
                    InventoryLockItemEntity.builder()
                            .lockId(lockId)
                            .skuId(skuIds.get(i))
                            .invDate(dates.get(i))
                            .quantity(quantities.get(i))
                            .build());
        }
        inventoryLockItemRepository.saveAll(lockItems);
        lockEntity.setItems(lockItems);

        lockedEntities.forEach(redisClient::cacheInventory);
        redisClient.addLockExpiry(lockId, expireAt);

        log.info("Inventory locked: lockId={}, orderId={}, expireAt={}", lockId, orderId, expireAt);
        return inventoryMapper.toLockProto(lockEntity);
    }

    /** Idempotent: if already CONFIRMED, returns success. */
    @Override
    @Transactional
    public InventoryLock confirmLock(String lockId) {
        log.debug("Confirming lock: {}", lockId);

        InventoryLockEntity lockEntity =
                inventoryLockRepository
                        .findByLockId(lockId)
                        .orElseThrow(() -> new NotFoundException("InventoryLock", lockId));

        if ("CONFIRMED".equals(lockEntity.getStatus())) {
            log.info("Lock {} already confirmed", lockId);
            return inventoryMapper.toLockProto(lockEntity);
        }

        if (!"LOCKED".equals(lockEntity.getStatus())) {
            throw new InvalidArgumentException(
                    "Lock "
                            + lockId
                            + " is in status "
                            + lockEntity.getStatus()
                            + ", cannot confirm");
        }

        List<InventoryLockItemEntity> lockItems = inventoryLockItemRepository.findByLockId(lockId);
        List<DailyInventoryEntity> updatedEntities = new ArrayList<>();

        for (InventoryLockItemEntity item : lockItems) {
            DailyInventoryEntity entity =
                    dailyInventoryRepository
                            .findBySkuIdAndInvDateForUpdate(item.getSkuId(), item.getInvDate())
                            .orElseThrow(
                                    () ->
                                            new NotFoundException(
                                                    "DailyInventory",
                                                    item.getSkuId() + "/" + item.getInvDate()));
            entity.setLockedQty(entity.getLockedQty() - item.getQuantity());
            entity.setSoldQty(entity.getSoldQty() + item.getQuantity());
            updatedEntities.add(entity);
        }

        dailyInventoryRepository.saveAll(updatedEntities);

        lockEntity.setStatus("CONFIRMED");
        lockEntity = inventoryLockRepository.save(lockEntity);
        lockEntity.setItems(lockItems);

        // Best-effort: sync Redis
        updatedEntities.forEach(redisClient::cacheInventory);
        redisClient.removeLockExpiry(lockId);

        log.info("Lock confirmed: {}", lockId);
        return inventoryMapper.toLockProto(lockEntity);
    }

    /** Idempotent: if already RELEASED/EXPIRED, returns success. */
    @Override
    @Transactional
    public InventoryLock releaseLock(String lockId, String reason) {
        log.debug("Releasing lock: {}, reason: {}", lockId, reason);

        InventoryLockEntity lockEntity =
                inventoryLockRepository
                        .findByLockId(lockId)
                        .orElseThrow(() -> new NotFoundException("InventoryLock", lockId));

        if ("RELEASED".equals(lockEntity.getStatus()) || "EXPIRED".equals(lockEntity.getStatus())) {
            log.info("Lock {} already {}", lockId, lockEntity.getStatus());
            return inventoryMapper.toLockProto(lockEntity);
        }

        if (!"LOCKED".equals(lockEntity.getStatus())) {
            throw new InvalidArgumentException(
                    "Lock "
                            + lockId
                            + " is in status "
                            + lockEntity.getStatus()
                            + ", cannot release");
        }

        List<InventoryLockItemEntity> lockItems = inventoryLockItemRepository.findByLockId(lockId);
        List<DailyInventoryEntity> updatedEntities = new ArrayList<>();

        for (InventoryLockItemEntity item : lockItems) {
            DailyInventoryEntity entity =
                    dailyInventoryRepository
                            .findBySkuIdAndInvDateForUpdate(item.getSkuId(), item.getInvDate())
                            .orElseThrow(
                                    () ->
                                            new NotFoundException(
                                                    "DailyInventory",
                                                    item.getSkuId() + "/" + item.getInvDate()));
            entity.setLockedQty(entity.getLockedQty() - item.getQuantity());
            entity.setAvailableQty(entity.getAvailableQty() + item.getQuantity());
            updatedEntities.add(entity);
        }

        dailyInventoryRepository.saveAll(updatedEntities);

        lockEntity.setStatus("RELEASED");
        lockEntity = inventoryLockRepository.save(lockEntity);
        lockEntity.setItems(lockItems);

        updatedEntities.forEach(redisClient::cacheInventory);
        redisClient.removeLockExpiry(lockId);

        log.info("Lock released: {}, reason: {}", lockId, reason);
        return inventoryMapper.toLockProto(lockEntity);
    }

    private DailyInventory buildDailyInventoryFromCache(
            String skuId, LocalDate date, Map<String, String> cached) {
        return DailyInventory.newBuilder()
                .setSkuId(skuId)
                .setDate(inventoryMapper.localDateToProto(date))
                .setTotalQuantity(Integer.parseInt(cached.getOrDefault("total", "0")))
                .setAvailableQuantity(Integer.parseInt(cached.getOrDefault("available", "0")))
                .setLockedQuantity(Integer.parseInt(cached.getOrDefault("locked", "0")))
                .setSoldQuantity(Integer.parseInt(cached.getOrDefault("sold", "0")))
                .setPrice(
                        org.tripsphere.common.v1.Money.newBuilder()
                                .setCurrency(cached.getOrDefault("price_ccy", "CNY"))
                                .setUnits(Long.parseLong(cached.getOrDefault("price_units", "0")))
                                .setNanos(Integer.parseInt(cached.getOrDefault("price_nanos", "0")))
                                .build())
                .build();
    }
}
