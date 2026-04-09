package org.tripsphere.order.application.service.query;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.tripsphere.order.application.exception.NotFoundException;
import org.tripsphere.order.application.port.OrderRepository;
import org.tripsphere.order.domain.model.Order;

@Slf4j
@Service
@RequiredArgsConstructor
public class GetOrderByNoUseCase {

    private final OrderRepository orderRepository;

    public Order execute(String orderNo) {
        log.debug("Getting order by order no: {}", orderNo);
        return orderRepository.findByOrderNo(orderNo).orElseThrow(() -> new NotFoundException("Order", orderNo));
    }
}
