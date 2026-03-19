package org.tripsphere.order.application.service.query;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.tripsphere.order.application.exception.NotFoundException;
import org.tripsphere.order.domain.model.Order;
import org.tripsphere.order.domain.repository.OrderRepository;

@Slf4j
@Service
@RequiredArgsConstructor
public class GetOrderUseCase {

    private final OrderRepository orderRepository;

    public Order execute(String orderId) {
        log.debug("Getting order: {}", orderId);
        return orderRepository.findById(orderId).orElseThrow(() -> new NotFoundException("Order", orderId));
    }
}
