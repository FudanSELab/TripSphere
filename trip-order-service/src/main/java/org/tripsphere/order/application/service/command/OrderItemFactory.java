package org.tripsphere.order.application.service.command;

import java.time.LocalDate;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Component;
import org.tripsphere.order.application.dto.CreateOrderItemCommand;
import org.tripsphere.order.application.dto.DailyInventoryInfo;
import org.tripsphere.order.application.dto.SkuInfo;
import org.tripsphere.order.application.dto.SpuInfo;
import org.tripsphere.order.application.port.InventoryPort;
import org.tripsphere.order.domain.model.Money;
import org.tripsphere.order.domain.model.OrderItem;

@Slf4j
@Component
@RequiredArgsConstructor
class OrderItemFactory {

    private final InventoryPort inventoryPort;

    record AssembledOrder(List<OrderItem> items, Money totalAmount) {}

    AssembledOrder assemble(
            List<CreateOrderItemCommand> commandItems,
            Map<String, SkuInfo> skuMap,
            Map<String, SpuInfo> spuMap,
            String orderId,
            String lockId,
            String resourceId) {

        Map<String, Money> priceCache = fetchPrices(commandItems, skuMap);

        List<OrderItem> orderItems = new ArrayList<>();
        long totalUnits = 0;
        int totalNanos = 0;
        String totalCurrency = "CNY";

        for (CreateOrderItemCommand createItem : commandItems) {
            SkuInfo sku = skuMap.get(createItem.skuId());
            SpuInfo spu = spuMap.get(sku.spuId());

            long itemSubtotalUnits = 0;
            int itemSubtotalNanos = 0;
            Money firstDayPrice = null;

            if (createItem.endDate() != null && createItem.endDate().isAfter(createItem.date())) {
                for (LocalDate d = createItem.date(); d.isBefore(createItem.endDate()); d = d.plusDays(1)) {
                    Money dayPrice = lookupPrice(sku, d, priceCache);
                    if (firstDayPrice == null) firstDayPrice = dayPrice;
                    itemSubtotalUnits += dayPrice.units() * createItem.quantity();
                    itemSubtotalNanos += dayPrice.nanos() * createItem.quantity();
                }
            } else {
                Money unitPrice = lookupPrice(sku, createItem.date(), priceCache);
                firstDayPrice = unitPrice;
                itemSubtotalUnits = unitPrice.units() * createItem.quantity();
                itemSubtotalNanos = unitPrice.nanos() * createItem.quantity();
            }

            itemSubtotalUnits += itemSubtotalNanos / 1_000_000_000;
            itemSubtotalNanos = itemSubtotalNanos % 1_000_000_000;

            if (firstDayPrice == null) firstDayPrice = sku.basePrice();
            totalCurrency = firstDayPrice.currency().isEmpty() ? "CNY" : firstDayPrice.currency();

            OrderItem orderItem = OrderItem.builder()
                    .id(UUID.randomUUID().toString())
                    .orderId(orderId)
                    .spuId(sku.spuId())
                    .skuId(sku.id())
                    .productName(spu != null ? spu.name() : sku.name())
                    .skuName(sku.name())
                    .resourceType(spu != null ? spu.resourceType() : null)
                    .resourceId(resourceId)
                    .spuImage(extractFirstImage(spu))
                    .spuDescription(spu != null ? spu.description() : null)
                    .skuAttributes(sku.attributes())
                    .itemDate(createItem.date())
                    .endDate(createItem.endDate())
                    .quantity(createItem.quantity())
                    .unitPrice(new Money(totalCurrency, firstDayPrice.units(), firstDayPrice.nanos()))
                    .subtotal(new Money(totalCurrency, itemSubtotalUnits, itemSubtotalNanos))
                    .invLockId(lockId)
                    .build();
            orderItems.add(orderItem);

            totalUnits += itemSubtotalUnits;
            totalNanos += itemSubtotalNanos;
        }

        totalUnits += totalNanos / 1_000_000_000;
        totalNanos = totalNanos % 1_000_000_000;

        return new AssembledOrder(orderItems, new Money(totalCurrency, totalUnits, totalNanos));
    }

    private Map<String, Money> fetchPrices(List<CreateOrderItemCommand> items, Map<String, SkuInfo> skuMap) {
        Map<String, List<LocalDate>> skuDatesMap = new LinkedHashMap<>();
        for (CreateOrderItemCommand item : items) {
            List<LocalDate> dates = skuDatesMap.computeIfAbsent(item.skuId(), k -> new ArrayList<>());
            if (item.endDate() != null && item.endDate().isAfter(item.date())) {
                for (LocalDate d = item.date(); d.isBefore(item.endDate()); d = d.plusDays(1)) {
                    dates.add(d);
                }
            } else {
                dates.add(item.date());
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
                List<DailyInventoryInfo> inventories = inventoryPort.queryInventoryCalendar(skuId, minDate, maxDate);
                for (DailyInventoryInfo inv : inventories) {
                    if (inv.price() != null && inv.price().units() > 0) {
                        priceCache.put(skuId + ":" + inv.date(), inv.price());
                    }
                }
            } catch (Exception e) {
                log.warn("Failed to fetch prices for sku={}, falling back to base price", skuId, e);
            }
        }
        return priceCache;
    }

    private Money lookupPrice(SkuInfo sku, LocalDate date, Map<String, Money> priceCache) {
        Money cached = priceCache.get(sku.id() + ":" + date);
        return cached != null ? cached : sku.basePrice();
    }

    private String extractFirstImage(SpuInfo spu) {
        if (spu == null || spu.images() == null || spu.images().isEmpty()) return null;
        String image = spu.images().getFirst();
        return image.isEmpty() ? null : image;
    }
}
