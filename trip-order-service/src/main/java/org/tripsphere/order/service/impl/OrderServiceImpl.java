package org.tripsphere.order.service.impl;

import java.time.Duration;
import java.time.Instant;
import java.time.LocalDate;
import java.time.format.DateTimeFormatter;
import java.util.List;
import java.util.Optional;
import java.util.Set;
import java.util.stream.Collectors;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.redis.core.StringRedisTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.tripsphere.order.exception.InvalidArgumentException;
import org.tripsphere.order.exception.NotFoundException;
import org.tripsphere.order.exception.OrderStateException;
import org.tripsphere.order.grpc.client.InventoryServiceClient;
import org.tripsphere.order.mapper.OrderMapper;
import org.tripsphere.order.model.OrderEntity;
import org.tripsphere.order.model.OrderItemEntity;
import org.tripsphere.order.repository.OrderItemRepository;
import org.tripsphere.order.repository.OrderRepository;
import org.tripsphere.order.saga.CreateOrderSaga;
import org.tripsphere.order.service.OrderService;
import org.tripsphere.order.v1.ContactInfo;
import org.tripsphere.order.v1.CreateOrderItem;
import org.tripsphere.order.v1.Order;
import org.tripsphere.order.v1.OrderSource;
import org.tripsphere.order.v1.OrderStatus;
import org.tripsphere.order.v1.OrderType;

@Slf4j
@Service
@RequiredArgsConstructor
public class OrderServiceImpl implements OrderService {

    private final OrderRepository orderRepository;
    private final OrderItemRepository orderItemRepository;
    private final CreateOrderSaga createOrderSaga;
    private final InventoryServiceClient inventoryClient;
    private final StringRedisTemplate redisTemplate;
    private final OrderMapper orderMapper = OrderMapper.INSTANCE;

    private static final String ORDER_EXPIRE_KEY = "order:expire";
    private static final String ORDER_DEDUP_KEY_PREFIX = "order:dedup:";
    private static final Duration DEDUP_WINDOW = Duration.ofSeconds(10);

    /** Not @Transactional: saga makes gRPC calls; DB tx only in persistOrder step. */
    @Override
    public Order createOrder(
            String userId, List<CreateOrderItem> items, ContactInfo contact, OrderSource source) {
        log.info("Creating order for user: {}, items: {}", userId, items.size());

        // --- Dedup: prevent duplicate submission within short time window ---
        checkDuplicateSubmission(userId, items);

        // Generate order number
        String orderNo = generateOrderNo();

        // Execute Saga (gRPC calls + transactional persist)
        OrderEntity order = createOrderSaga.execute(userId, items, contact, source, orderNo);

        // Add to Redis expiry sorted set
        if (order.getExpireAt() != null) {
            try {
                redisTemplate
                        .opsForZSet()
                        .add(ORDER_EXPIRE_KEY, order.getId(), order.getExpireAt());
            } catch (Exception e) {
                log.warn("Failed to add order expiry to Redis: {}", e.getMessage());
            }
        }

        return orderMapper.toProto(order);
    }

    @Override
    public Optional<Order> getOrder(String orderId) {
        log.debug("Getting order: {}", orderId);
        return orderRepository
                .findById(orderId)
                .map(
                        entity -> {
                            List<OrderItemEntity> items =
                                    orderItemRepository.findByOrderId(orderId);
                            entity.setItems(items);
                            return orderMapper.toProto(entity);
                        });
    }

    @Override
    public Page<Order> listUserOrders(
            String userId, OrderStatus status, OrderType type, int pageSize, String pageToken) {
        log.debug(
                "Listing orders: userId={}, status={}, type={}, pageSize={}, pageToken={}",
                userId,
                status,
                type,
                pageSize,
                pageToken);

        int page = 0;
        if (pageToken != null && !pageToken.isEmpty()) {
            try {
                page = Integer.parseInt(pageToken);
            } catch (NumberFormatException e) {
                log.warn("Invalid page token: {}", pageToken);
            }
        }
        if (pageSize <= 0) pageSize = 20;
        if (pageSize > 100) pageSize = 100;

        String statusStr =
                (status != null && status != OrderStatus.ORDER_STATUS_UNSPECIFIED)
                        ? orderMapper.orderStatusToString(status)
                        : null;
        String typeStr =
                (type != null && type != OrderType.ORDER_TYPE_UNSPECIFIED)
                        ? orderMapper.orderTypeToString(type)
                        : null;

        PageRequest pageable = PageRequest.of(page, pageSize);
        Page<OrderEntity> entityPage;

        if (statusStr != null && typeStr != null) {
            entityPage =
                    orderRepository.findByUserIdAndStatusAndTypeOrderByCreatedAtDesc(
                            userId, statusStr, typeStr, pageable);
        } else if (statusStr != null) {
            entityPage =
                    orderRepository.findByUserIdAndStatusOrderByCreatedAtDesc(
                            userId, statusStr, pageable);
        } else if (typeStr != null) {
            entityPage =
                    orderRepository.findByUserIdAndTypeOrderByCreatedAtDesc(
                            userId, typeStr, pageable);
        } else {
            entityPage = orderRepository.findByUserIdOrderByCreatedAtDesc(userId, pageable);
        }

        return entityPage.map(
                entity -> {
                    List<OrderItemEntity> items = orderItemRepository.findByOrderId(entity.getId());
                    entity.setItems(items);
                    return orderMapper.toProto(entity);
                });
    }

    @Override
    @Transactional
    public Order cancelOrder(String orderId, String reason) {
        log.info("Cancelling order: {}, reason: {}", orderId, reason);

        OrderEntity order =
                orderRepository
                        .findById(orderId)
                        .orElseThrow(() -> new NotFoundException("Order", orderId));

        if (!"PENDING_PAYMENT".equals(order.getStatus())) {
            throw new OrderStateException(orderId, order.getStatus(), "PENDING_PAYMENT");
        }

        List<OrderItemEntity> items = orderItemRepository.findByOrderId(orderId);
        Set<String> lockIds =
                items.stream()
                        .map(OrderItemEntity::getInvLockId)
                        .filter(id -> id != null && !id.isEmpty())
                        .collect(Collectors.toSet());

        for (String lockId : lockIds) {
            try {
                inventoryClient.releaseLock(lockId, reason);
            } catch (Exception e) {
                log.error("Failed to release inventory lock: {} for order: {}", lockId, orderId, e);
            }
        }

        long now = Instant.now().getEpochSecond();
        order.setStatus("CANCELLED");
        order.setCancelReason(reason);
        order.setCancelledAt(now);
        order.setUpdatedAt(now);
        order = orderRepository.save(order);
        order.setItems(items);

        try {
            redisTemplate.opsForZSet().remove(ORDER_EXPIRE_KEY, orderId);
        } catch (Exception e) {
            log.warn("Failed to remove order expiry from Redis: {}", e.getMessage());
        }

        log.info("Order cancelled: {}", orderId);
        return orderMapper.toProto(order);
    }

    @Override
    @Transactional
    public Order confirmPayment(String orderId, String paymentMethod) {
        log.info("Confirming payment for order: {}, method: {}", orderId, paymentMethod);

        OrderEntity order =
                orderRepository
                        .findById(orderId)
                        .orElseThrow(() -> new NotFoundException("Order", orderId));

        if (!"PENDING_PAYMENT".equals(order.getStatus())) {
            throw new OrderStateException(orderId, order.getStatus(), "PENDING_PAYMENT");
        }

        // Check if order has expired
        long now = Instant.now().getEpochSecond();
        if (order.getExpireAt() != null && now > order.getExpireAt()) {
            throw new OrderStateException("Order " + orderId + " has expired");
        }

        List<OrderItemEntity> items = orderItemRepository.findByOrderId(orderId);
        Set<String> lockIds =
                items.stream()
                        .map(OrderItemEntity::getInvLockId)
                        .filter(id -> id != null && !id.isEmpty())
                        .collect(Collectors.toSet());

        for (String lockId : lockIds) {
            try {
                inventoryClient.confirmLock(lockId);
            } catch (Exception e) {
                log.error("Failed to confirm inventory lock: {} for order: {}", lockId, orderId, e);
                throw new RuntimeException("Failed to confirm inventory for order: " + orderId, e);
            }
        }

        order.setStatus("PAID");
        order.setPaidAt(now);
        order.setUpdatedAt(now);
        order = orderRepository.save(order);
        order.setItems(items);

        try {
            redisTemplate.opsForZSet().remove(ORDER_EXPIRE_KEY, orderId);
        } catch (Exception e) {
            log.warn("Failed to remove order expiry from Redis: {}", e.getMessage());
        }

        log.info("Payment confirmed for order: {}", orderId);
        return orderMapper.toProto(order);
    }

    /** Dedup by userId + items fingerprint. Fail-open if Redis unavailable. */
    private void checkDuplicateSubmission(String userId, List<CreateOrderItem> items) {
        try {
            String fingerprint =
                    items.stream()
                            .map(
                                    i ->
                                            i.getSkuId()
                                                    + ":"
                                                    + i.getDate().getYear()
                                                    + "-"
                                                    + i.getDate().getMonth()
                                                    + "-"
                                                    + i.getDate().getDay()
                                                    + ":"
                                                    + i.getQuantity())
                            .sorted()
                            .collect(Collectors.joining("|"));

            String dedupKey =
                    ORDER_DEDUP_KEY_PREFIX
                            + userId
                            + ":"
                            + Integer.toHexString(fingerprint.hashCode());

            Boolean isNew = redisTemplate.opsForValue().setIfAbsent(dedupKey, "1", DEDUP_WINDOW);
            if (!Boolean.TRUE.equals(isNew)) {
                throw new InvalidArgumentException(
                        "Duplicate order submission detected. Please wait a moment before"
                                + " retrying.");
            }
        } catch (InvalidArgumentException e) {
            throw e; // Re-throw business exception
        } catch (Exception e) {
            log.warn("Redis dedup check failed, proceeding without dedup: {}", e.getMessage());
        }
    }

    /**
     * Generate order number: TS + yyyyMMdd + 6-digit sequence. Uses PostgreSQL SEQUENCE for atomic,
     * concurrency-safe generation.
     */
    private String generateOrderNo() {
        String today = LocalDate.now().format(DateTimeFormatter.ofPattern("yyyyMMdd"));
        long seq = orderRepository.getNextOrderSequence();
        return String.format("TS%s%06d", today, seq);
    }
}
