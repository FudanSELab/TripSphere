package org.tripsphere.order.application.service.command;

import java.time.LocalDate;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.function.Function;
import java.util.stream.Collectors;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Component;
import org.tripsphere.order.application.dto.CreateOrderCommand;
import org.tripsphere.order.application.dto.CreateOrderItemCommand;
import org.tripsphere.order.application.dto.SkuInfo;
import org.tripsphere.order.application.dto.SpuInfo;
import org.tripsphere.order.application.exception.InvalidArgumentException;
import org.tripsphere.order.application.port.ProductPort;
import org.tripsphere.order.domain.model.OrderType;

@Component
@RequiredArgsConstructor
class OrderValidator {
    private final ProductPort productPort;

    record ValidatedOrderContext(
            Map<String, SkuInfo> skuMap, Map<String, SpuInfo> spuMap, String resourceId, OrderType orderType) {}

    ValidatedOrderContext validate(CreateOrderCommand command) {
        Map<String, SkuInfo> skuMap = fetchAndValidateSkus(command.items());
        Map<String, SpuInfo> spuMap = fetchSpus(skuMap);
        OrderContext ctx = validateHomogeneity(command.items(), skuMap, spuMap);
        return new ValidatedOrderContext(skuMap, spuMap, ctx.resourceId(), ctx.orderType());
    }

    private record OrderContext(String resourceId, OrderType orderType) {}

    private Map<String, SkuInfo> fetchAndValidateSkus(List<CreateOrderItemCommand> items) {
        List<String> skuIds =
                items.stream().map(CreateOrderItemCommand::skuId).distinct().toList();

        List<SkuInfo> skus = productPort.batchGetSkus(skuIds);
        Map<String, SkuInfo> skuMap = skus.stream().collect(Collectors.toMap(SkuInfo::id, Function.identity()));

        for (String skuId : skuIds) {
            SkuInfo sku = skuMap.get(skuId);
            if (sku == null) throw new InvalidArgumentException("SKU not found: " + skuId);
            if (!sku.active()) throw new InvalidArgumentException("SKU is not active: " + skuId);
        }
        return skuMap;
    }

    private Map<String, SpuInfo> fetchSpus(Map<String, SkuInfo> skuMap) {
        List<String> spuIds = skuMap.values().stream()
                .map(SkuInfo::spuId)
                .filter(id -> !id.isEmpty())
                .distinct()
                .toList();

        List<SpuInfo> spus = productPort.batchGetSpus(spuIds);
        return spus.stream().collect(Collectors.toMap(SpuInfo::id, Function.identity()));
    }

    private OrderContext validateHomogeneity(
            List<CreateOrderItemCommand> items, Map<String, SkuInfo> skuMap, Map<String, SpuInfo> spuMap) {

        Set<String> resourceTypes = items.stream()
                .map(item -> requireSpu(skuMap, spuMap, item).resourceType())
                .collect(Collectors.toSet());

        if (resourceTypes.size() > 1) {
            throw new InvalidArgumentException("All items must have the same resource type, found: " + resourceTypes);
        }

        String resourceType = resourceTypes.iterator().next();
        if ("UNSPECIFIED".equals(resourceType) || resourceType == null) {
            throw new InvalidArgumentException("Order items have unspecified resource type");
        }

        Set<String> topLevelIds = new HashSet<>();
        for (CreateOrderItemCommand item : items) {
            SpuInfo spu = requireSpu(skuMap, spuMap, item);
            topLevelIds.add(extractTopLevelResourceId(spu, resourceType));
        }

        if (topLevelIds.size() > 1) {
            String entityLabel = "HOTEL_ROOM".equals(resourceType) ? "hotel" : "attraction";
            throw new InvalidArgumentException("All items must belong to the same " + entityLabel);
        }

        validateDateConsistency(items, resourceType);

        return new OrderContext(topLevelIds.iterator().next(), resourceTypeToOrderType(resourceType));
    }

    private String extractTopLevelResourceId(SpuInfo spu, String resourceType) {
        return switch (resourceType) {
            case "HOTEL_ROOM" -> {
                Object hotelIdObj = spu.attributes() != null ? spu.attributes().get("hotel_id") : null;
                String hotelId = hotelIdObj != null ? hotelIdObj.toString() : "";
                if (hotelId.isEmpty()) {
                    throw new InvalidArgumentException("SPU " + spu.id() + " is missing hotel_id in attributes");
                }
                yield hotelId;
            }
            case "ATTRACTION" -> spu.resourceId();
            default -> throw new InvalidArgumentException("Unsupported resource type: " + resourceType);
        };
    }

    private void validateDateConsistency(List<CreateOrderItemCommand> items, String resourceType) {
        Set<LocalDate> startDates =
                items.stream().map(CreateOrderItemCommand::date).collect(Collectors.toSet());

        if (startDates.size() > 1) {
            throw new InvalidArgumentException("All items must share the same date");
        }

        if ("HOTEL_ROOM".equals(resourceType)) {
            for (CreateOrderItemCommand item : items) {
                if (item.endDate() == null) {
                    throw new InvalidArgumentException("Hotel room items must have an end_date (check-out date)");
                }
            }
            Set<LocalDate> endDates =
                    items.stream().map(CreateOrderItemCommand::endDate).collect(Collectors.toSet());
            if (endDates.size() > 1) {
                throw new InvalidArgumentException("All hotel room items must share the same check-out date");
            }
            LocalDate checkIn = items.getFirst().date();
            LocalDate checkOut = items.getFirst().endDate();
            if (!checkOut.isAfter(checkIn)) {
                throw new InvalidArgumentException("Check-out date must be after check-in date");
            }
        } else {
            for (CreateOrderItemCommand item : items) {
                if (item.endDate() != null) {
                    throw new InvalidArgumentException("Attraction ticket items must not have an end_date");
                }
            }
        }
    }

    private SpuInfo requireSpu(Map<String, SkuInfo> skuMap, Map<String, SpuInfo> spuMap, CreateOrderItemCommand item) {
        SkuInfo sku = skuMap.get(item.skuId());
        SpuInfo spu = spuMap.get(sku.spuId());
        if (spu == null) {
            throw new InvalidArgumentException("SPU not found for SKU: " + item.skuId());
        }
        return spu;
    }

    private OrderType resourceTypeToOrderType(String resourceType) {
        return switch (resourceType) {
            case "HOTEL_ROOM" -> OrderType.HOTEL;
            case "ATTRACTION" -> OrderType.ATTRACTION;
            default -> OrderType.UNSPECIFIED;
        };
    }
}
