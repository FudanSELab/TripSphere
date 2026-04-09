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
import org.tripsphere.order.domain.model.Order;

@Slf4j
@Service
@RequiredArgsConstructor
public class ConfirmPaymentUseCase {

    private final OrderRepository orderRepository;
    private final InventoryPort inventoryPort;
    private final OrderCachePort cachePort;

    @Transactional
    public Order execute(String orderId, String paymentMethod) {
        log.info("Confirming payment for order: {}, method: {}", orderId, paymentMethod);

        Order order = orderRepository.findById(orderId).orElseThrow(() -> new NotFoundException("Order", orderId));

        confirmInventoryLocks(order);

        order.confirmPayment();
        order = orderRepository.save(order);
        cachePort.removeOrderExpiry(orderId);

        log.info("Payment confirmed for order: {}", orderId);
        return order;
    }

    private void confirmInventoryLocks(Order order) {
        for (String lockId : order.getDistinctLockIds()) {
            try {
                inventoryPort.confirmLock(lockId);
            } catch (Exception e) {
                log.error("Failed to confirm inventory lock: {} for order: {}", lockId, order.getId(), e);
                throw new OrderStateException("Failed to confirm inventory for order: " + order.getId());
            }
        }
    }
}
