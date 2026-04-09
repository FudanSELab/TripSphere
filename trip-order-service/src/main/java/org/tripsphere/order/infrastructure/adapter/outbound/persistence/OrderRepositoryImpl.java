package org.tripsphere.order.infrastructure.adapter.outbound.persistence;

import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.stream.Collectors;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.stereotype.Repository;
import org.tripsphere.order.application.dto.ListOrdersQuery;
import org.tripsphere.order.application.dto.OrderPage;
import org.tripsphere.order.application.port.OrderRepository;
import org.tripsphere.order.domain.model.Order;
import org.tripsphere.order.infrastructure.adapter.outbound.persistence.entity.OrderEntity;
import org.tripsphere.order.infrastructure.adapter.outbound.persistence.entity.OrderItemEntity;
import org.tripsphere.order.infrastructure.adapter.outbound.persistence.mapper.OrderEntityMapper;

@Repository
@RequiredArgsConstructor
public class OrderRepositoryImpl implements OrderRepository {

    private final OrderJpaRepository orderJpaRepository;
    private final OrderItemJpaRepository orderItemJpaRepository;
    private final OrderEntityMapper mapper;

    @Override
    public Order save(Order order) {
        OrderEntity entity = mapper.toEntity(order);
        entity = orderJpaRepository.save(entity);

        List<OrderItemEntity> itemEntities = mapper.toItemEntities(order.getItems());
        if (!itemEntities.isEmpty()) {
            orderItemJpaRepository.saveAll(itemEntities);
        }

        List<OrderItemEntity> savedItems = orderItemJpaRepository.findByOrderId(order.getId());
        return mapper.toDomain(entity, savedItems);
    }

    @Override
    public Optional<Order> findById(String id) {
        return orderJpaRepository.findById(id).map(entity -> {
            List<OrderItemEntity> items = orderItemJpaRepository.findByOrderId(id);
            return mapper.toDomain(entity, items);
        });
    }

    @Override
    public Optional<Order> findByOrderNo(String orderNo) {
        return orderJpaRepository.findByOrderNo(orderNo).map(entity -> {
            List<OrderItemEntity> items = orderItemJpaRepository.findByOrderId(entity.getId());
            return mapper.toDomain(entity, items);
        });
    }

    @Override
    public OrderPage findByUserIdWithFilters(ListOrdersQuery query) {
        int pageSize = query.pageSize() <= 0 ? 20 : Math.min(query.pageSize(), 100);
        PageRequest pageable = PageRequest.of(query.page(), pageSize);

        String statusStr = query.status() != null ? query.status().name() : null;
        String typeStr = query.type() != null ? query.type().name() : null;

        Page<OrderEntity> entityPage = findOrderEntities(query.userId(), statusStr, typeStr, pageable);

        List<String> orderIds =
                entityPage.getContent().stream().map(OrderEntity::getId).toList();

        Map<String, List<OrderItemEntity>> itemsByOrderId = orderItemJpaRepository.findByOrderIdIn(orderIds).stream()
                .collect(Collectors.groupingBy(OrderItemEntity::getOrderId));

        List<Order> orders = entityPage.getContent().stream()
                .map(entity -> mapper.toDomain(entity, itemsByOrderId.getOrDefault(entity.getId(), List.of())))
                .toList();

        return new OrderPage(orders, entityPage.getTotalPages(), entityPage.hasNext(), entityPage.getNumber());
    }

    @Override
    public long getNextOrderSequence() {
        return orderJpaRepository.getNextOrderSequence();
    }

    @Override
    public void createSequenceIfNotExists() {
        orderJpaRepository.createOrderSequenceIfNotExists();
    }

    private Page<OrderEntity> findOrderEntities(String userId, String status, String type, PageRequest pageable) {
        if (status != null && type != null) {
            return orderJpaRepository.findByUserIdAndStatusAndTypeOrderByCreatedAtDesc(userId, status, type, pageable);
        } else if (status != null) {
            return orderJpaRepository.findByUserIdAndStatusOrderByCreatedAtDesc(userId, status, pageable);
        } else if (type != null) {
            return orderJpaRepository.findByUserIdAndTypeOrderByCreatedAtDesc(userId, type, pageable);
        } else {
            return orderJpaRepository.findByUserIdOrderByCreatedAtDesc(userId, pageable);
        }
    }
}
