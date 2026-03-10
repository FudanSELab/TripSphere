package org.tripsphere.order.saga;

import java.time.Instant;
import java.time.LocalDate;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.stream.Collectors;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;
import org.springframework.transaction.PlatformTransactionManager;
import org.springframework.transaction.support.TransactionTemplate;
import org.tripsphere.common.v1.Money;
import org.tripsphere.inventory.v1.DailyInventory;
import org.tripsphere.inventory.v1.InventoryLock;
import org.tripsphere.inventory.v1.LockItem;
import org.tripsphere.order.exception.InvalidArgumentException;
import org.tripsphere.order.grpc.client.InventoryServiceClient;
import org.tripsphere.order.grpc.client.ProductServiceClient;
import org.tripsphere.order.mapper.OrderMapper;
import org.tripsphere.order.model.OrderEntity;
import org.tripsphere.order.model.OrderItemEntity;
import org.tripsphere.order.repository.OrderItemRepository;
import org.tripsphere.order.repository.OrderRepository;
import org.tripsphere.order.v1.ContactInfo;
import org.tripsphere.order.v1.CreateOrderItem;
import org.tripsphere.order.v1.OrderSource;
import org.tripsphere.product.v1.Sku;
import org.tripsphere.product.v1.SkuStatus;
import org.tripsphere.product.v1.Spu;

/** CreateOrder saga: validate SKUs → lock inventory → persist order. Compensates on failure. */
@Slf4j
@Component
@RequiredArgsConstructor
public class CreateOrderSaga {

    private final ProductServiceClient productClient;
    private final InventoryServiceClient inventoryClient;
    private final OrderRepository orderRepository;
    private final OrderItemRepository orderItemRepository;
    private final PlatformTransactionManager transactionManager;
    private final OrderMapper orderMapper = OrderMapper.INSTANCE;

    private static final int ORDER_EXPIRE_SECONDS = 900;

    public OrderEntity execute(
            String userId,
            List<CreateOrderItem> items,
            ContactInfo contact,
            OrderSource source,
            String orderNo) {

        log.info("Starting CreateOrder saga for user: {}, items: {}", userId, items.size());

        // Step 1: Validate SKUs
        List<String> skuIds = items.stream().map(CreateOrderItem::getSkuId).distinct().toList();
        List<Sku> skus = productClient.batchGetSkus(skuIds);

        Map<String, Sku> skuMap = skus.stream().collect(Collectors.toMap(Sku::getId, sku -> sku));

        // Validate all requested SKUs exist and are active
        for (String skuId : skuIds) {
            Sku sku = skuMap.get(skuId);
            if (sku == null) {
                throw new InvalidArgumentException("SKU not found: " + skuId);
            }
            if (sku.getStatus() != SkuStatus.SKU_STATUS_ACTIVE) {
                throw new InvalidArgumentException("SKU is not active: " + skuId);
            }
        }

        // Step 1.5: Fetch SPU names for snapshots
        Map<String, String> spuNameMap = fetchSpuNames(skus);

        // Step 2: Lock inventory
        String orderId = UUID.randomUUID().toString();
        List<LockItem> lockItems = buildLockItems(items);

        InventoryLock inventoryLock;
        try {
            inventoryLock = inventoryClient.lockInventory(lockItems, orderId, ORDER_EXPIRE_SECONDS);
        } catch (Exception e) {
            log.error("Failed to lock inventory for order: {}", orderId, e);
            throw e;
        }

        // Step 2.5: Fetch prices
        Map<String, Money> priceCache = fetchPrices(items, skuMap);

        // Step 3: Persist order
        try {
            return persistOrder(
                    orderId,
                    orderNo,
                    userId,
                    items,
                    contact,
                    source,
                    skuMap,
                    spuNameMap,
                    priceCache,
                    inventoryLock);
        } catch (Exception e) {
            // Compensation: release locked inventory
            log.error(
                    "Failed to create order locally, releasing inventory lock: {}",
                    inventoryLock.getLockId(),
                    e);
            try {
                inventoryClient.releaseLock(
                        inventoryLock.getLockId(), "Order creation failed: " + e.getMessage());
            } catch (Exception releaseEx) {
                log.error(
                        "Failed to release inventory lock: {}",
                        inventoryLock.getLockId(),
                        releaseEx);
            }
            throw e;
        }
    }

    private Map<String, String> fetchSpuNames(List<Sku> skus) {
        List<String> spuIds =
                skus.stream().map(Sku::getSpuId).filter(id -> !id.isEmpty()).distinct().toList();

        Map<String, String> spuNameMap = new HashMap<>();
        if (!spuIds.isEmpty()) {
            try {
                List<Spu> spus = productClient.batchGetSpus(spuIds);
                for (Spu spu : spus) {
                    spuNameMap.put(spu.getId(), spu.getName());
                }
            } catch (Exception e) {
                log.warn("Failed to batch fetch SPU names, will use SKU names as fallback", e);
            }
        }
        return spuNameMap;
    }

    /** Build lock items. Expands hotel date ranges into individual nights. */
    private List<LockItem> buildLockItems(List<CreateOrderItem> items) {
        List<LockItem> lockItems = new ArrayList<>();
        for (CreateOrderItem item : items) {
            LocalDate startDate = orderMapper.protoToLocalDate(item.getDate());
            LocalDate endDate =
                    item.hasEndDate() ? orderMapper.protoToLocalDate(item.getEndDate()) : null;

            if (endDate != null && endDate.isAfter(startDate)) {
                for (LocalDate d = startDate; d.isBefore(endDate); d = d.plusDays(1)) {
                    lockItems.add(
                            LockItem.newBuilder()
                                    .setSkuId(item.getSkuId())
                                    .setDate(orderMapper.localDateToProto(d))
                                    .setQuantity(item.getQuantity())
                                    .build());
                }
            } else {
                lockItems.add(
                        LockItem.newBuilder()
                                .setSkuId(item.getSkuId())
                                .setDate(item.getDate())
                                .setQuantity(item.getQuantity())
                                .build());
            }
        }
        return lockItems;
    }

    /** Fetch prices for all (sku, date) combinations via calendar queries. */
    private Map<String, Money> fetchPrices(List<CreateOrderItem> items, Map<String, Sku> skuMap) {

        Map<String, List<LocalDate>> skuDatesMap = new LinkedHashMap<>();
        for (CreateOrderItem item : items) {
            LocalDate startDate = orderMapper.protoToLocalDate(item.getDate());
            LocalDate endDate =
                    item.hasEndDate() ? orderMapper.protoToLocalDate(item.getEndDate()) : null;

            List<LocalDate> dates =
                    skuDatesMap.computeIfAbsent(item.getSkuId(), k -> new ArrayList<>());

            if (endDate != null && endDate.isAfter(startDate)) {
                for (LocalDate d = startDate; d.isBefore(endDate); d = d.plusDays(1)) {
                    dates.add(d);
                }
            } else {
                dates.add(startDate);
            }
        }

        Map<String, Money> priceCache = new HashMap<>();
        for (Map.Entry<String, List<LocalDate>> entry : skuDatesMap.entrySet()) {
            String skuId = entry.getKey();
            List<LocalDate> dates = entry.getValue();
            LocalDate minDate = dates.stream().min(LocalDate::compareTo).orElse(null);
            LocalDate maxDate = dates.stream().max(LocalDate::compareTo).orElse(null);

            if (minDate == null) continue;

            try {
                List<DailyInventory> inventories =
                        inventoryClient.queryInventoryCalendar(
                                skuId,
                                orderMapper.localDateToProto(minDate),
                                orderMapper.localDateToProto(maxDate));
                for (DailyInventory inv : inventories) {
                    if (inv.hasPrice() && inv.getPrice().getUnits() > 0) {
                        LocalDate invDate = orderMapper.protoToLocalDate(inv.getDate());
                        priceCache.put(skuId + ":" + invDate, inv.getPrice());
                    }
                }
            } catch (Exception e) {
                log.warn("Failed to fetch inventory prices for sku={}, using base price", skuId, e);
            }
        }

        return priceCache;
    }

    /** Persist order in a dedicated DB transaction. */
    private OrderEntity persistOrder(
            String orderId,
            String orderNo,
            String userId,
            List<CreateOrderItem> items,
            ContactInfo contact,
            OrderSource source,
            Map<String, Sku> skuMap,
            Map<String, String> spuNameMap,
            Map<String, Money> priceCache,
            InventoryLock inventoryLock) {

        TransactionTemplate txTemplate = new TransactionTemplate(transactionManager);
        return txTemplate.execute(
                status -> {
                    long now = Instant.now().getEpochSecond();

                    List<OrderItemEntity> orderItems = new ArrayList<>();
                    long totalUnits = 0;
                    int totalNanos = 0;
                    String totalCurrency = "CNY";

                    for (CreateOrderItem createItem : items) {
                        Sku sku = skuMap.get(createItem.getSkuId());
                        String itemId = UUID.randomUUID().toString();

                        LocalDate startDate = orderMapper.protoToLocalDate(createItem.getDate());
                        LocalDate endDate =
                                createItem.hasEndDate()
                                        ? orderMapper.protoToLocalDate(createItem.getEndDate())
                                        : null;

                        long itemSubtotalUnits = 0;
                        int itemSubtotalNanos = 0;
                        Money firstDayPrice = null;

                        if (endDate != null && endDate.isAfter(startDate)) {
                            for (LocalDate d = startDate; d.isBefore(endDate); d = d.plusDays(1)) {
                                Money dayPrice =
                                        lookupPrice(createItem.getSkuId(), d, priceCache, sku);
                                if (firstDayPrice == null) firstDayPrice = dayPrice;
                                itemSubtotalUnits += dayPrice.getUnits() * createItem.getQuantity();
                                itemSubtotalNanos += dayPrice.getNanos() * createItem.getQuantity();
                            }
                        } else {
                            Money unitPrice =
                                    lookupPrice(createItem.getSkuId(), startDate, priceCache, sku);
                            firstDayPrice = unitPrice;
                            itemSubtotalUnits = unitPrice.getUnits() * createItem.getQuantity();
                            itemSubtotalNanos = unitPrice.getNanos() * createItem.getQuantity();
                        }

                        itemSubtotalUnits += itemSubtotalNanos / 1_000_000_000;
                        itemSubtotalNanos = itemSubtotalNanos % 1_000_000_000;

                        if (firstDayPrice == null) {
                            firstDayPrice = sku.getBasePrice();
                        }
                        totalCurrency =
                                firstDayPrice.getCurrency().isEmpty()
                                        ? "CNY"
                                        : firstDayPrice.getCurrency();

                        String productName = spuNameMap.getOrDefault(sku.getSpuId(), sku.getName());

                        OrderItemEntity orderItem =
                                OrderItemEntity.builder()
                                        .id(itemId)
                                        .orderId(orderId)
                                        .spuId(sku.getSpuId())
                                        .skuId(sku.getId())
                                        .productName(productName)
                                        .skuName(sku.getName())
                                        .itemDate(startDate)
                                        .endDate(endDate)
                                        .quantity(createItem.getQuantity())
                                        .unitPriceCcy(totalCurrency)
                                        .unitPriceUnits(firstDayPrice.getUnits())
                                        .unitPriceNanos(firstDayPrice.getNanos())
                                        .subtotalCcy(totalCurrency)
                                        .subtotalUnits(itemSubtotalUnits)
                                        .subtotalNanos(itemSubtotalNanos)
                                        .invLockId(inventoryLock.getLockId())
                                        .build();
                        orderItems.add(orderItem);

                        totalUnits += itemSubtotalUnits;
                        totalNanos += itemSubtotalNanos;
                    }

                    totalUnits += totalNanos / 1_000_000_000;
                    totalNanos = totalNanos % 1_000_000_000;

                    OrderEntity order =
                            OrderEntity.builder()
                                    .id(orderId)
                                    .orderNo(orderNo)
                                    .userId(userId)
                                    .status("PENDING_PAYMENT")
                                    .totalCurrency(totalCurrency)
                                    .totalUnits(totalUnits)
                                    .totalNanos(totalNanos)
                                    .contactName(contact != null ? contact.getName() : null)
                                    .contactPhone(contact != null ? contact.getPhone() : null)
                                    .contactEmail(contact != null ? contact.getEmail() : null)
                                    .sourceChannel(source != null ? source.getChannel() : null)
                                    .sourceAgentId(source != null ? source.getAgentId() : null)
                                    .sourceSession(source != null ? source.getSessionId() : null)
                                    .expireAt(now + ORDER_EXPIRE_SECONDS)
                                    .createdAt(now)
                                    .updatedAt(now)
                                    .build();

                    order = orderRepository.save(order);
                    orderItemRepository.saveAll(orderItems);
                    order.setItems(orderItems);

                    log.info(
                            "Order created: id={}, orderNo={}, total={}",
                            orderId,
                            orderNo,
                            totalUnits);
                    return order;
                });
    }

    private Money lookupPrice(
            String skuId, LocalDate date, Map<String, Money> priceCache, Sku sku) {
        Money cached = priceCache.get(skuId + ":" + date);
        if (cached != null) {
            return cached;
        }
        return sku.getBasePrice();
    }
}
