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
public class GetOrderByNoUseCase {

    private final OrderRepository orderRepository;
    private final OrderAuthorizationService authorizationService;

    public Order execute(String currentUserId, String orderNo) {
        log.debug(
                "Getting order by order no: request_id={}, order_no={}",
                CorrelationContext.currentRequestId(),
                orderNo);
        Order order = orderRepository.findByOrderNo(orderNo).orElseThrow(() -> new NotFoundException("Order", orderNo));
        authorizationService.requireOrderOwner(currentUserId, order);
        return order;
    }
}
