package org.tripsphere.order.application.service.command;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.tripsphere.order.application.exception.NotFoundException;
import org.tripsphere.order.application.exception.OrderStateException;
import org.tripsphere.order.application.port.InventoryPort;
import org.tripsphere.order.application.port.OrderCachePort;
import org.tripsphere.order.application.port.OrderRepository;
import org.tripsphere.order.application.service.OrderAuthorizationService;
import org.tripsphere.order.domain.model.Order;

@Slf4j
@Service
@RequiredArgsConstructor
public class CancelOrderUseCase {

    private final OrderRepository orderRepository;
    private final InventoryPort inventoryPort;
    private final OrderCachePort cachePort;
    private final OrderAuthorizationService authorizationService;

    @Transactional
    public Order execute(String orderId, String reason) {
        return execute(orderId, reason, null);
    }

    @Transactional
    public Order executeForUser(String currentUserId, String orderId, String reason) {
        return execute(orderId, reason, currentUserId);
    }

    private Order execute(String orderId, String reason, String currentUserId) {
        log.info("Cancelling order: {}, reason: {}", orderId, reason);

        Order order = orderRepository.findById(orderId).orElseThrow(() -> new NotFoundException("Order", orderId));
        if (currentUserId != null) {
            authorizationService.requireOrderOwner(currentUserId, order);
        }

        order.validateCanCancel();
        releaseInventory(order, reason);

        order.cancel(reason);
        order = orderRepository.save(order);
        cachePort.removeOrderExpiry(orderId);

        log.info("Order cancelled: {}", orderId);
        return order;
    }

    private void releaseInventory(Order order, String reason) {
        for (String lockId : order.getDistinctLockIds()) {
            try {
                inventoryPort.releaseLock(lockId, reason);
            } catch (Exception e) {
                log.error("Failed to release inventory lock: {} for order: {}", lockId, order.getId(), e);
                throw new OrderStateException("Failed to release inventory for order: " + order.getId());
            }
        }
    }
}
