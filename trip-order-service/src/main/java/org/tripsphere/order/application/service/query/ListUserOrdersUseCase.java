package org.tripsphere.order.application.service.query;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.tripsphere.order.application.dto.ListOrdersQuery;
import org.tripsphere.order.application.dto.OrderPage;
import org.tripsphere.order.application.port.OrderQueryPort;

@Slf4j
@Service
@RequiredArgsConstructor
public class ListUserOrdersUseCase {

    private final OrderQueryPort orderQueryPort;

    public OrderPage execute(ListOrdersQuery query) {
        log.debug(
                "Listing orders: userId={}, status={}, type={}, pageSize={}, page={}",
                query.userId(),
                query.status(),
                query.type(),
                query.pageSize(),
                query.page());

        return orderQueryPort.findByUserIdWithFilters(query);
    }
}
