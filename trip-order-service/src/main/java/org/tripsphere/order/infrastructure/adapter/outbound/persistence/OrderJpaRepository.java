package org.tripsphere.order.infrastructure.adapter.outbound.persistence;

import java.util.Optional;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Modifying;
import org.springframework.data.jpa.repository.Query;
import org.springframework.transaction.annotation.Transactional;
import org.tripsphere.order.infrastructure.adapter.outbound.persistence.entity.OrderEntity;

public interface OrderJpaRepository extends JpaRepository<OrderEntity, String> {

    Optional<OrderEntity> findByOrderNo(String orderNo);

    @Query(value = "SELECT nextval('order_no_seq')", nativeQuery = true)
    long getNextOrderSequence();

    @Modifying
    @Transactional
    @Query(value = "CREATE SEQUENCE IF NOT EXISTS order_no_seq START 1", nativeQuery = true)
    void createOrderSequenceIfNotExists();

    Page<OrderEntity> findByUserIdOrderByCreatedAtDesc(String userId, Pageable pageable);

    Page<OrderEntity> findByUserIdAndStatusOrderByCreatedAtDesc(String userId, String status, Pageable pageable);

    Page<OrderEntity> findByUserIdAndTypeOrderByCreatedAtDesc(String userId, String type, Pageable pageable);

    Page<OrderEntity> findByUserIdAndStatusAndTypeOrderByCreatedAtDesc(
            String userId, String status, String type, Pageable pageable);
}
