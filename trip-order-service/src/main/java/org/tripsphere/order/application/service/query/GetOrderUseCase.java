package org.tripsphere.order.application.service.query;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.tripsphere.order.application.exception.NotFoundException;
import org.tripsphere.order.application.port.OrderRepository;
import org.tripsphere.order.application.service.OrderAuthorizationService;
import org.tripsphere.order.domain.model.Order;
import org.tripsphere.order.infrastructure.observability.CorrelationContext;

@Slf4j
@Service
@RequiredArgsConstructor
public class GetOrderUseCase {

    private final OrderRepository orderRepository;
    private final OrderAuthorizationService authorizationService;

    public Order execute(String currentUserId, String orderId) {
        log.debug("Getting order: request_id={}, order_id={}", CorrelationContext.currentRequestId(), orderId);
        Order order = orderRepository.findById(orderId).orElseThrow(() -> new NotFoundException("Order", orderId));
        authorizationService.requireOrderOwner(currentUserId, order);
        return order;
    }
}
