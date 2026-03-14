package org.tripsphere.order.saga;

import com.google.protobuf.Struct;
import com.google.protobuf.Value;
import com.google.protobuf.util.JsonFormat;
import java.time.Instant;
import java.time.LocalDate;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.UUID;
import java.util.stream.Collectors;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;
import org.springframework.transaction.PlatformTransactionManager;
import org.springframework.transaction.support.TransactionTemplate;
import org.tripsphere.common.v1.Date;
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
import org.tripsphere.product.v1.ResourceType;
import org.tripsphere.product.v1.Sku;
import org.tripsphere.product.v1.SkuStatus;
import org.tripsphere.product.v1.Spu;

/** CreateOrder saga: validate → check homogeneity → lock inventory → persist. */
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

    /** Holds the validated order-level context derived from homogeneity checks. */
    private record OrderContext(String resourceId, String orderType) {}

    public OrderEntity execute(
            String userId,
            List<CreateOrderItem> items,
            ContactInfo contact,
            OrderSource source,
            String orderNo) {

        log.info("Starting CreateOrder saga for user: {}, items: {}", userId, items.size());

        // Step 1: Validate SKUs exist and are active.
        List<String> skuIds = items.stream().map(CreateOrderItem::getSkuId).distinct().toList();
        List<Sku> skus = productClient.batchGetSkus(skuIds);
        Map<String, Sku> skuMap = skus.stream().collect(Collectors.toMap(Sku::getId, s -> s));

        for (String skuId : skuIds) {
            Sku sku = skuMap.get(skuId);
            if (sku == null) throw new InvalidArgumentException("SKU not found: " + skuId);
            if (sku.getStatus() != SkuStatus.SKU_STATUS_ACTIVE)
                throw new InvalidArgumentException("SKU is not active: " + skuId);
        }

        // Step 2: Fetch full SPU data for homogeneity validation and snapshots.
        Map<String, Spu> spuMap = fetchSpus(skus);

        // Step 3: Validate all items belong to the same resource with consistent dates.
        OrderContext ctx = validateAndGetContext(items, skuMap, spuMap);

        // Step 4: Lock inventory.
        String orderId = UUID.randomUUID().toString();
        List<LockItem> lockItems = buildLockItems(items);

        InventoryLock inventoryLock;
        try {
            inventoryLock = inventoryClient.lockInventory(lockItems, orderId, ORDER_EXPIRE_SECONDS);
        } catch (Exception e) {
            log.error("Failed to lock inventory for order: {}", orderId, e);
            throw e;
        }

        // Step 5: Fetch daily prices from inventory calendar.
        Map<String, Money> priceCache = fetchPrices(items, skuMap);

        // Step 6: Persist order in a DB transaction; compensate on failure.
        try {
            return persistOrder(
                    orderId,
                    orderNo,
                    userId,
                    items,
                    contact,
                    source,
                    skuMap,
                    spuMap,
                    priceCache,
                    inventoryLock,
                    ctx.orderType(),
                    ctx.resourceId());
        } catch (Exception e) {
            log.error(
                    "Failed to persist order, releasing inventory lock: {}",
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

    // ---------------------------------------------------------------------------
    // Validation
    // ---------------------------------------------------------------------------

    /**
     * Validates that all items belong to the same resource (same hotel or same attraction) and
     * share identical dates. Returns the derived top-level resource ID and order type.
     */
    private OrderContext validateAndGetContext(
            List<CreateOrderItem> items, Map<String, Sku> skuMap, Map<String, Spu> spuMap) {

        // All SPUs must share the same resource_type.
        Set<ResourceType> resourceTypes =
                items.stream()
                        .map(item -> requireSpu(skuMap, spuMap, item).getResourceType())
                        .collect(Collectors.toSet());

        if (resourceTypes.size() > 1) {
            throw new InvalidArgumentException(
                    "All items must have the same resource type, found: " + resourceTypes);
        }

        ResourceType resourceType = resourceTypes.iterator().next();
        if (resourceType == ResourceType.RESOURCE_TYPE_UNSPECIFIED) {
            throw new InvalidArgumentException("Order items have unspecified resource type");
        }

        // Derive the top-level resource ID for each item and verify uniqueness.
        Set<String> topLevelIds = new HashSet<>();
        for (CreateOrderItem item : items) {
            Spu spu = requireSpu(skuMap, spuMap, item);
            topLevelIds.add(extractTopLevelResourceId(spu, resourceType));
        }

        if (topLevelIds.size() > 1) {
            String entityLabel =
                    resourceType == ResourceType.RESOURCE_TYPE_HOTEL_ROOM ? "hotel" : "attraction";
            throw new InvalidArgumentException("All items must belong to the same " + entityLabel);
        }

        validateDateConsistency(items, resourceType);

        return new OrderContext(
                topLevelIds.iterator().next(), resourceTypeToOrderType(resourceType));
    }

    /**
     * For HOTEL_ROOM: reads "hotel_id" from SPU attributes. For ATTRACTION: uses spu.resource_id
     * directly (which is the attraction ID).
     */
    private String extractTopLevelResourceId(Spu spu, ResourceType resourceType) {
        return switch (resourceType) {
            case RESOURCE_TYPE_HOTEL_ROOM -> {
                Value hotelIdValue =
                        spu.getAttributes()
                                .getFieldsOrDefault("hotel_id", Value.getDefaultInstance());
                String hotelId = hotelIdValue.getStringValue();
                if (hotelId.isEmpty()) {
                    throw new InvalidArgumentException(
                            "SPU " + spu.getId() + " is missing hotel_id in attributes");
                }
                yield hotelId;
            }
            case RESOURCE_TYPE_ATTRACTION -> spu.getResourceId();
            default -> throw new InvalidArgumentException(
                    "Unsupported resource type: " + resourceType);
        };
    }

    private void validateDateConsistency(List<CreateOrderItem> items, ResourceType resourceType) {
        Set<String> startDates =
                items.stream()
                        .map(
                                i ->
                                        i.getDate().getYear()
                                                + "-"
                                                + i.getDate().getMonth()
                                                + "-"
                                                + i.getDate().getDay())
                        .collect(Collectors.toSet());

        if (startDates.size() > 1) {
            throw new InvalidArgumentException("All items must share the same date");
        }

        if (resourceType == ResourceType.RESOURCE_TYPE_HOTEL_ROOM) {
            for (CreateOrderItem item : items) {
                if (!item.hasEndDate() || isDateEmpty(item.getEndDate())) {
                    throw new InvalidArgumentException(
                            "Hotel room items must have an end_date (check-out date)");
                }
            }

            Set<String> endDates =
                    items.stream()
                            .map(
                                    i ->
                                            i.getEndDate().getYear()
                                                    + "-"
                                                    + i.getEndDate().getMonth()
                                                    + "-"
                                                    + i.getEndDate().getDay())
                            .collect(Collectors.toSet());

            if (endDates.size() > 1) {
                throw new InvalidArgumentException(
                        "All hotel room items must share the same check-out date");
            }

            LocalDate checkIn = orderMapper.protoToLocalDate(items.get(0).getDate());
            LocalDate checkOut = orderMapper.protoToLocalDate(items.get(0).getEndDate());
            if (!checkOut.isAfter(checkIn)) {
                throw new InvalidArgumentException("Check-out date must be after check-in date");
            }
        } else {
            for (CreateOrderItem item : items) {
                if (item.hasEndDate() && !isDateEmpty(item.getEndDate())) {
                    throw new InvalidArgumentException(
                            "Attraction ticket items must not have an end_date");
                }
            }
        }
    }

    // ---------------------------------------------------------------------------
    // Data fetching
    // ---------------------------------------------------------------------------

    private Map<String, Spu> fetchSpus(List<Sku> skus) {
        List<String> spuIds =
                skus.stream().map(Sku::getSpuId).filter(id -> !id.isEmpty()).distinct().toList();

        if (spuIds.isEmpty()) return Map.of();

        List<Spu> spus = productClient.batchGetSpus(spuIds);
        return spus.stream().collect(Collectors.toMap(Spu::getId, s -> s));
    }

    /** Expands hotel date ranges into per-night lock items. */
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
                log.warn("Failed to fetch prices for sku={}, falling back to base price", skuId, e);
            }
        }

        return priceCache;
    }

    // ---------------------------------------------------------------------------
    // Persistence
    // ---------------------------------------------------------------------------

    private OrderEntity persistOrder(
            String orderId,
            String orderNo,
            String userId,
            List<CreateOrderItem> items,
            ContactInfo contact,
            OrderSource source,
            Map<String, Sku> skuMap,
            Map<String, Spu> spuMap,
            Map<String, Money> priceCache,
            InventoryLock inventoryLock,
            String orderType,
            String resourceId) {

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
                        Spu spu = spuMap.get(sku.getSpuId());

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
                                Money dayPrice = lookupPrice(sku.getId(), d, priceCache, sku);
                                if (firstDayPrice == null) firstDayPrice = dayPrice;
                                itemSubtotalUnits += dayPrice.getUnits() * createItem.getQuantity();
                                itemSubtotalNanos += dayPrice.getNanos() * createItem.getQuantity();
                            }
                        } else {
                            Money unitPrice = lookupPrice(sku.getId(), startDate, priceCache, sku);
                            firstDayPrice = unitPrice;
                            itemSubtotalUnits = unitPrice.getUnits() * createItem.getQuantity();
                            itemSubtotalNanos = unitPrice.getNanos() * createItem.getQuantity();
                        }

                        itemSubtotalUnits += itemSubtotalNanos / 1_000_000_000;
                        itemSubtotalNanos = itemSubtotalNanos % 1_000_000_000;

                        if (firstDayPrice == null) firstDayPrice = sku.getBasePrice();
                        totalCurrency =
                                firstDayPrice.getCurrency().isEmpty()
                                        ? "CNY"
                                        : firstDayPrice.getCurrency();

                        OrderItemEntity orderItem =
                                OrderItemEntity.builder()
                                        .id(UUID.randomUUID().toString())
                                        .orderId(orderId)
                                        .spuId(sku.getSpuId())
                                        .skuId(sku.getId())
                                        .productName(spu != null ? spu.getName() : sku.getName())
                                        .skuName(sku.getName())
                                        .resourceType(normalizeResourceType(spu))
                                        .resourceId(resourceId)
                                        .spuImage(extractFirstImage(spu))
                                        .spuDescription(extractDescription(spu))
                                        .skuAttributes(structToMap(sku.getAttributes()))
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
                                    .type(orderType)
                                    .resourceId(resourceId)
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
                            "Order created: id={}, orderNo={}, type={}, resourceId={}",
                            orderId,
                            orderNo,
                            orderType,
                            resourceId);
                    return order;
                });
    }

    // ---------------------------------------------------------------------------
    // Helpers
    // ---------------------------------------------------------------------------

    private Money lookupPrice(
            String skuId, LocalDate date, Map<String, Money> priceCache, Sku sku) {
        Money cached = priceCache.get(skuId + ":" + date);
        return cached != null ? cached : sku.getBasePrice();
    }

    private Spu requireSpu(Map<String, Sku> skuMap, Map<String, Spu> spuMap, CreateOrderItem item) {
        Sku sku = skuMap.get(item.getSkuId());
        Spu spu = spuMap.get(sku.getSpuId());
        if (spu == null) {
            throw new InvalidArgumentException("SPU not found for SKU: " + item.getSkuId());
        }
        return spu;
    }

    private String resourceTypeToOrderType(ResourceType rt) {
        return switch (rt) {
            case RESOURCE_TYPE_HOTEL_ROOM -> "HOTEL";
            case RESOURCE_TYPE_ATTRACTION -> "ATTRACTION";
            default -> "UNSPECIFIED";
        };
    }

    private String normalizeResourceType(Spu spu) {
        if (spu == null) return null;
        return switch (spu.getResourceType()) {
            case RESOURCE_TYPE_HOTEL_ROOM -> "HOTEL_ROOM";
            case RESOURCE_TYPE_ATTRACTION -> "ATTRACTION";
            default -> null;
        };
    }

    private String extractFirstImage(Spu spu) {
        if (spu == null || spu.getImagesList().isEmpty()) return null;
        String image = spu.getImages(0);
        return image.isEmpty() ? null : image;
    }

    private String extractDescription(Spu spu) {
        if (spu == null || spu.getDescription().isEmpty()) return null;
        return spu.getDescription();
    }

    private Map<String, Object> structToMap(Struct struct) {
        if (struct == null || struct.getFieldsCount() == 0) return null;
        try {
            String json = JsonFormat.printer().print(struct);
            return new com.fasterxml.jackson.databind.ObjectMapper()
                    .readValue(json, new com.fasterxml.jackson.core.type.TypeReference<>() {});
        } catch (Exception e) {
            log.warn("Failed to convert struct to map: {}", e.getMessage());
            return null;
        }
    }

    private boolean isDateEmpty(Date date) {
        return date == null || (date.getYear() == 0 && date.getMonth() == 0 && date.getDay() == 0);
    }
}
