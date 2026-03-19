package org.tripsphere.order.adapter.outbound.persistence.mapper;

import java.util.ArrayList;
import java.util.List;
import org.mapstruct.Mapper;
import org.mapstruct.Mapping;
import org.mapstruct.MappingConstants;
import org.mapstruct.NullValueCheckStrategy;
import org.tripsphere.order.adapter.outbound.persistence.entity.OrderEntity;
import org.tripsphere.order.adapter.outbound.persistence.entity.OrderItemEntity;
import org.tripsphere.order.domain.model.*;

@Mapper(componentModel = MappingConstants.ComponentModel.SPRING, nullValueCheckStrategy = NullValueCheckStrategy.ALWAYS)
public interface OrderEntityMapper {

    // ── Order → Entity ───────────────────────────────────────

    @Mapping(target = "totalCurrency", source = "totalAmount.currency")
    @Mapping(target = "totalUnits", source = "totalAmount.units")
    @Mapping(target = "totalNanos", source = "totalAmount.nanos")
    @Mapping(target = "contactName", source = "contact.name")
    @Mapping(target = "contactPhone", source = "contact.phone")
    @Mapping(target = "contactEmail", source = "contact.email")
    @Mapping(target = "sourceChannel", source = "source.channel")
    @Mapping(target = "sourceAgentId", source = "source.agentId")
    @Mapping(target = "sourceSession", source = "source.sessionId")
    @Mapping(target = "items", ignore = true)
    OrderEntity toEntity(Order domain);

    // ── Entity → Order ───────────────────────────────────────

    default Order toDomain(OrderEntity entity, List<OrderItemEntity> itemEntities) {
        if (entity == null) return null;
        return Order.builder()
                .id(entity.getId())
                .orderNo(entity.getOrderNo())
                .userId(entity.getUserId())
                .status(OrderStatus.valueOf(entity.getStatus()))
                .type(OrderType.valueOf(entity.getType()))
                .resourceId(entity.getResourceId())
                .totalAmount(new Money(entity.getTotalCurrency(), entity.getTotalUnits(), entity.getTotalNanos()))
                .contact(new ContactInfo(entity.getContactName(), entity.getContactPhone(), entity.getContactEmail()))
                .source(new OrderSource(
                        entity.getSourceChannel(), entity.getSourceAgentId(), entity.getSourceSession()))
                .cancelReason(entity.getCancelReason())
                .expireAt(entity.getExpireAt())
                .createdAt(entity.getCreatedAt())
                .updatedAt(entity.getUpdatedAt())
                .paidAt(entity.getPaidAt())
                .cancelledAt(entity.getCancelledAt())
                .items(
                        itemEntities != null
                                ? new ArrayList<>(itemEntities.stream()
                                        .map(this::toItemDomain)
                                        .toList())
                                : new ArrayList<>())
                .build();
    }

    // ── OrderItem → Entity ───────────────────────────────────

    @Mapping(target = "unitPriceCcy", source = "unitPrice.currency")
    @Mapping(target = "unitPriceUnits", source = "unitPrice.units")
    @Mapping(target = "unitPriceNanos", source = "unitPrice.nanos")
    @Mapping(target = "subtotalCcy", source = "subtotal.currency")
    @Mapping(target = "subtotalUnits", source = "subtotal.units")
    @Mapping(target = "subtotalNanos", source = "subtotal.nanos")
    OrderItemEntity toItemEntity(OrderItem domain);

    // ── Entity → OrderItem ───────────────────────────────────

    @Mapping(
            target = "unitPrice",
            expression =
                    "java(toMoney(entity.getUnitPriceCcy(), entity.getUnitPriceUnits(), entity.getUnitPriceNanos()))")
    @Mapping(
            target = "subtotal",
            expression = "java(toMoney(entity.getSubtotalCcy(), entity.getSubtotalUnits(), entity.getSubtotalNanos()))")
    OrderItem toItemDomain(OrderItemEntity entity);

    List<OrderItemEntity> toItemEntities(List<OrderItem> items);

    // ── Helpers ──────────────────────────────────────────────

    default String mapOrderStatus(OrderStatus status) {
        return status != null ? status.name() : null;
    }

    default String mapOrderType(OrderType type) {
        return type != null ? type.name() : null;
    }

    default Money toMoney(String currency, Long units, Integer nanos) {
        if (currency == null) return null;
        return new Money(currency, units != null ? units : 0L, nanos != null ? nanos : 0);
    }
}
