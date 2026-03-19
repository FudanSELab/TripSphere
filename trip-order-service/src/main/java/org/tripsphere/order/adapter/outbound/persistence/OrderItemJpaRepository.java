package org.tripsphere.order.adapter.outbound.persistence;

import java.util.Collection;
import java.util.List;
import org.springframework.data.jpa.repository.JpaRepository;
import org.tripsphere.order.adapter.outbound.persistence.entity.OrderItemEntity;

public interface OrderItemJpaRepository extends JpaRepository<OrderItemEntity, String> {

    List<OrderItemEntity> findByOrderId(String orderId);

    List<OrderItemEntity> findByOrderIdIn(Collection<String> orderIds);
}
