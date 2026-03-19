package org.tripsphere.order.adapter.inbound.grpc.mapper;

import com.google.protobuf.Timestamp;
import java.util.List;
import org.mapstruct.*;
import org.tripsphere.order.domain.model.*;

@Mapper(
        componentModel = MappingConstants.ComponentModel.SPRING,
        collectionMappingStrategy = CollectionMappingStrategy.ADDER_PREFERRED,
        nullValueCheckStrategy = NullValueCheckStrategy.ALWAYS,
        uses = {MoneyProtoMapper.class, DateProtoMapper.class, StructProtoMapper.class})
public interface OrderProtoMapper {

    // ── Order ────────────────────────────────────────────────

    org.tripsphere.order.v1.Order toProto(Order domain);

    List<org.tripsphere.order.v1.Order> toProtos(List<Order> domains);

    // ── OrderItem ────────────────────────────────────────────

    @Mapping(source = "productName", target = "spuName")
    @Mapping(source = "itemDate", target = "date")
    @Mapping(source = "invLockId", target = "inventoryLockId")
    org.tripsphere.order.v1.OrderItem toItemProto(OrderItem item);

    // ── OrderStatus ──────────────────────────────────────────

    @ValueMapping(source = "PENDING_PAYMENT", target = "ORDER_STATUS_PENDING_PAYMENT")
    @ValueMapping(source = "PAID", target = "ORDER_STATUS_PAID")
    @ValueMapping(source = "COMPLETED", target = "ORDER_STATUS_COMPLETED")
    @ValueMapping(source = "CANCELLED", target = "ORDER_STATUS_CANCELLED")
    org.tripsphere.order.v1.OrderStatus mapStatus(OrderStatus status);

    default OrderStatus mapStatusToDomain(org.tripsphere.order.v1.OrderStatus proto) {
        return switch (proto) {
            case ORDER_STATUS_PENDING_PAYMENT -> OrderStatus.PENDING_PAYMENT;
            case ORDER_STATUS_PAID -> OrderStatus.PAID;
            case ORDER_STATUS_COMPLETED -> OrderStatus.COMPLETED;
            case ORDER_STATUS_CANCELLED -> OrderStatus.CANCELLED;
            default -> null;
        };
    }

    // ── OrderType ────────────────────────────────────────────

    @ValueMapping(source = "UNSPECIFIED", target = "ORDER_TYPE_UNSPECIFIED")
    @ValueMapping(source = "ATTRACTION", target = "ORDER_TYPE_ATTRACTION")
    @ValueMapping(source = "HOTEL", target = "ORDER_TYPE_HOTEL")
    @ValueMapping(source = "FLIGHT", target = "ORDER_TYPE_FLIGHT")
    @ValueMapping(source = "TRAIN", target = "ORDER_TYPE_TRAIN")
    org.tripsphere.order.v1.OrderType mapType(OrderType type);

    default OrderType mapTypeToDomain(org.tripsphere.order.v1.OrderType proto) {
        return switch (proto) {
            case ORDER_TYPE_ATTRACTION -> OrderType.ATTRACTION;
            case ORDER_TYPE_HOTEL -> OrderType.HOTEL;
            case ORDER_TYPE_FLIGHT -> OrderType.FLIGHT;
            case ORDER_TYPE_TRAIN -> OrderType.TRAIN;
            default -> null;
        };
    }

    // ── Nested message types ─────────────────────────────────

    org.tripsphere.order.v1.ContactInfo mapContact(ContactInfo contact);

    org.tripsphere.order.v1.OrderSource mapSource(OrderSource source);

    // ── Timestamp helpers ────────────────────────────────────

    default Timestamp mapToTimestamp(long epoch) {
        return Timestamp.newBuilder().setSeconds(epoch).build();
    }

    default Timestamp mapToTimestamp(Long epoch) {
        return epoch != null ? Timestamp.newBuilder().setSeconds(epoch).build() : null;
    }
}
