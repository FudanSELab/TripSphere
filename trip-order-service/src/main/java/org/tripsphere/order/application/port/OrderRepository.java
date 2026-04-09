package org.tripsphere.order.application.port;

import java.util.Optional;
import org.tripsphere.order.application.dto.ListOrdersQuery;
import org.tripsphere.order.application.dto.OrderPage;
import org.tripsphere.order.domain.model.Order;

public interface OrderRepository {

    Order save(Order order);

    Optional<Order> findById(String id);

    Optional<Order> findByOrderNo(String orderNo);

    long getNextOrderSequence();

    void createSequenceIfNotExists();

    OrderPage findByUserIdWithFilters(ListOrdersQuery query);
}
