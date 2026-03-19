package org.tripsphere.order.application.service.command;

import java.time.LocalDate;
import java.util.ArrayList;
import java.util.List;
import java.util.UUID;
import java.util.stream.Collectors;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.tripsphere.order.application.dto.CreateOrderCommand;
import org.tripsphere.order.application.dto.CreateOrderItemCommand;
import org.tripsphere.order.application.dto.LockItemData;
import org.tripsphere.order.application.exception.InvalidArgumentException;
import org.tripsphere.order.application.port.InventoryPort;
import org.tripsphere.order.application.port.OrderCachePort;
import org.tripsphere.order.config.OrderProperties;
import org.tripsphere.order.domain.model.Order;
import org.tripsphere.order.domain.repository.OrderRepository;

@Slf4j
@Service
@RequiredArgsConstructor
public class CreateOrderUseCase {

    private final OrderRepository orderRepository;
    private final InventoryPort inventoryPort;
    private final OrderCachePort cachePort;
    private final OrderValidator validator;
    private final OrderItemFactory itemFactory;
    private final OrderProperties properties;

    public Order execute(CreateOrderCommand command) {
        log.info(
                "Creating order for user: {}, items: {}",
                command.userId(),
                command.items().size());

        checkDuplicateSubmission(command);

        OrderValidator.ValidatedOrderContext ctx = validator.validate(command);

        String orderId = UUID.randomUUID().toString();
        String orderNo = generateOrderNo();
        List<LockItemData> lockItems = buildLockItems(command.items());

        String lockId = lockInventory(lockItems, orderId);

        try {
            return persistOrderAndCacheExpiry(orderId, orderNo, command, ctx, lockId);
        } catch (Exception e) {
            log.error("Failed to persist order, releasing inventory lock: {}", lockId, e);
            releaseInventoryQuietly(lockId, "Order creation failed: " + e.getMessage());
            throw e;
        }
    }

    private String lockInventory(List<LockItemData> lockItems, String orderId) {
        try {
            return inventoryPort.lockInventory(lockItems, orderId, properties.expireSeconds());
        } catch (Exception e) {
            log.error("Failed to lock inventory for order: {}", orderId, e);
            throw e;
        }
    }

    @Transactional
    protected Order persistOrderAndCacheExpiry(
            String orderId,
            String orderNo,
            CreateOrderCommand command,
            OrderValidator.ValidatedOrderContext ctx,
            String lockId) {

        OrderItemFactory.AssembledOrder assembled =
                itemFactory.assemble(command.items(), ctx.skuMap(), ctx.spuMap(), orderId, lockId, ctx.resourceId());

        long now = java.time.Instant.now().getEpochSecond();
        Order order = Order.create(
                orderId,
                orderNo,
                command.userId(),
                ctx.orderType(),
                ctx.resourceId(),
                assembled.totalAmount(),
                command.contact(),
                command.source(),
                now + properties.expireSeconds(),
                assembled.items());

        order = orderRepository.save(order);

        if (order.getExpireAt() != null) {
            cachePort.addOrderExpiry(order.getId(), order.getExpireAt());
        }

        log.info(
                "Order created: id={}, orderNo={}, type={}, resourceId={}",
                orderId,
                orderNo,
                ctx.orderType(),
                ctx.resourceId());
        return order;
    }

    private void releaseInventoryQuietly(String lockId, String reason) {
        try {
            inventoryPort.releaseLock(lockId, reason);
        } catch (Exception releaseEx) {
            log.error("Failed to release inventory lock: {}", lockId, releaseEx);
        }
    }

    private List<LockItemData> buildLockItems(List<CreateOrderItemCommand> items) {
        List<LockItemData> lockItems = new ArrayList<>();
        for (CreateOrderItemCommand item : items) {
            if (item.endDate() != null && item.endDate().isAfter(item.date())) {
                for (LocalDate d = item.date(); d.isBefore(item.endDate()); d = d.plusDays(1)) {
                    lockItems.add(new LockItemData(item.skuId(), d, item.quantity()));
                }
            } else {
                lockItems.add(new LockItemData(item.skuId(), item.date(), item.quantity()));
            }
        }
        return lockItems;
    }

    private void checkDuplicateSubmission(CreateOrderCommand command) {
        String fingerprint = command.items().stream()
                .map(i -> i.skuId() + ":" + i.date() + ":" + i.quantity())
                .sorted()
                .collect(Collectors.joining("|"));

        if (!cachePort.tryAcquireDedup(command.userId(), fingerprint)) {
            throw new InvalidArgumentException(
                    "Duplicate order submission detected. Please wait a moment before retrying.");
        }
    }

    private String generateOrderNo() {
        String today = LocalDate.now().format(java.time.format.DateTimeFormatter.ofPattern("yyyyMMdd"));
        long seq = orderRepository.getNextOrderSequence();
        return String.format("TS%s%06d", today, seq);
    }
}
