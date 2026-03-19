package org.tripsphere.order.domain.repository;

import java.util.Optional;
import org.tripsphere.order.domain.model.Order;

public interface OrderRepository {

    Order save(Order order);

    Optional<Order> findById(String id);

    long getNextOrderSequence();

    void createSequenceIfNotExists();
}
