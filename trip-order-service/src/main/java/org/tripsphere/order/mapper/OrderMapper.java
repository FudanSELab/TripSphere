package org.tripsphere.order.mapper;

import com.google.protobuf.Struct;
import com.google.protobuf.Timestamp;
import com.google.protobuf.util.JsonFormat;
import java.time.LocalDate;
import java.util.List;
import java.util.Map;
import org.mapstruct.*;
import org.mapstruct.factory.Mappers;
import org.tripsphere.common.v1.Date;
import org.tripsphere.common.v1.Money;
import org.tripsphere.order.model.OrderEntity;
import org.tripsphere.order.model.OrderItemEntity;
import org.tripsphere.order.v1.*;

@Mapper(
        collectionMappingStrategy = CollectionMappingStrategy.ADDER_PREFERRED,
        unmappedTargetPolicy = ReportingPolicy.IGNORE,
        nullValueCheckStrategy = NullValueCheckStrategy.ALWAYS)
public interface OrderMapper {
    OrderMapper INSTANCE = Mappers.getMapper(OrderMapper.class);

    default Order toProto(OrderEntity entity) {
        if (entity == null) return null;
        Order.Builder builder =
                Order.newBuilder()
                        .setId(entity.getId())
                        .setOrderNo(entity.getOrderNo())
                        .setUserId(entity.getUserId())
                        .setStatus(stringToOrderStatus(entity.getStatus()))
                        .setType(stringToOrderType(entity.getType()))
                        .setTotalAmount(
                                Money.newBuilder()
                                        .setCurrency(entity.getTotalCurrency())
                                        .setUnits(entity.getTotalUnits())
                                        .setNanos(entity.getTotalNanos())
                                        .build())
                        .setCreatedAt(epochSecondToTimestamp(entity.getCreatedAt()))
                        .setUpdatedAt(epochSecondToTimestamp(entity.getUpdatedAt()));

        if (entity.getResourceId() != null) builder.setResourceId(entity.getResourceId());

        if (entity.getContactName() != null
                || entity.getContactPhone() != null
                || entity.getContactEmail() != null) {
            ContactInfo.Builder contactBuilder = ContactInfo.newBuilder();
            if (entity.getContactName() != null) contactBuilder.setName(entity.getContactName());
            if (entity.getContactPhone() != null) contactBuilder.setPhone(entity.getContactPhone());
            if (entity.getContactEmail() != null) contactBuilder.setEmail(entity.getContactEmail());
            builder.setContact(contactBuilder.build());
        }

        if (entity.getSourceChannel() != null
                || entity.getSourceAgentId() != null
                || entity.getSourceSession() != null) {
            OrderSource.Builder sourceBuilder = OrderSource.newBuilder();
            if (entity.getSourceChannel() != null)
                sourceBuilder.setChannel(entity.getSourceChannel());
            if (entity.getSourceAgentId() != null)
                sourceBuilder.setAgentId(entity.getSourceAgentId());
            if (entity.getSourceSession() != null)
                sourceBuilder.setSessionId(entity.getSourceSession());
            builder.setSource(sourceBuilder.build());
        }

        if (entity.getCancelReason() != null) builder.setCancelReason(entity.getCancelReason());
        if (entity.getExpireAt() != null)
            builder.setExpireAt(epochSecondToTimestamp(entity.getExpireAt()));
        if (entity.getPaidAt() != null)
            builder.setPaidAt(epochSecondToTimestamp(entity.getPaidAt()));
        if (entity.getCancelledAt() != null)
            builder.setCancelledAt(epochSecondToTimestamp(entity.getCancelledAt()));

        if (entity.getItems() != null) {
            for (OrderItemEntity item : entity.getItems()) {
                builder.addItems(toItemProto(item));
            }
        }

        return builder.build();
    }

    default List<Order> toProtoList(List<OrderEntity> entities) {
        if (entities == null) return List.of();
        return entities.stream().map(this::toProto).toList();
    }

    default OrderItem toItemProto(OrderItemEntity entity) {
        if (entity == null) return null;
        OrderItem.Builder builder =
                OrderItem.newBuilder()
                        .setId(entity.getId())
                        .setSpuId(entity.getSpuId())
                        .setSkuId(entity.getSkuId())
                        .setQuantity(entity.getQuantity());

        if (entity.getProductName() != null) builder.setSpuName(entity.getProductName());
        if (entity.getSkuName() != null) builder.setSkuName(entity.getSkuName());
        if (entity.getItemDate() != null) builder.setDate(localDateToProto(entity.getItemDate()));
        if (entity.getEndDate() != null) builder.setEndDate(localDateToProto(entity.getEndDate()));
        if (entity.getInvLockId() != null) builder.setInventoryLockId(entity.getInvLockId());
        if (entity.getSpuImage() != null) builder.setSpuImage(entity.getSpuImage());
        if (entity.getSpuDescription() != null)
            builder.setSpuDescription(entity.getSpuDescription());
        if (entity.getResourceId() != null) builder.setResourceId(entity.getResourceId());

        if (entity.getSkuAttributes() != null) {
            Struct struct = mapToStruct(entity.getSkuAttributes());
            if (struct != null) builder.setSkuAttributes(struct);
        }

        if (entity.getUnitPriceUnits() != null) {
            builder.setUnitPrice(
                    Money.newBuilder()
                            .setCurrency(
                                    entity.getUnitPriceCcy() != null
                                            ? entity.getUnitPriceCcy()
                                            : "CNY")
                            .setUnits(entity.getUnitPriceUnits())
                            .setNanos(
                                    entity.getUnitPriceNanos() != null
                                            ? entity.getUnitPriceNanos()
                                            : 0)
                            .build());
        }

        if (entity.getSubtotalUnits() != null) {
            builder.setSubtotal(
                    Money.newBuilder()
                            .setCurrency(
                                    entity.getSubtotalCcy() != null
                                            ? entity.getSubtotalCcy()
                                            : "CNY")
                            .setUnits(entity.getSubtotalUnits())
                            .setNanos(
                                    entity.getSubtotalNanos() != null
                                            ? entity.getSubtotalNanos()
                                            : 0)
                            .build());
        }

        return builder.build();
    }

    default LocalDate protoToLocalDate(Date date) {
        if (date == null || (date.getYear() == 0 && date.getMonth() == 0 && date.getDay() == 0)) {
            return null;
        }
        return LocalDate.of(date.getYear(), date.getMonth(), date.getDay());
    }

    default Date localDateToProto(LocalDate date) {
        if (date == null) return Date.getDefaultInstance();
        return Date.newBuilder()
                .setYear(date.getYear())
                .setMonth(date.getMonthValue())
                .setDay(date.getDayOfMonth())
                .build();
    }

    default String orderStatusToString(OrderStatus status) {
        return switch (status) {
            case ORDER_STATUS_PENDING_PAYMENT -> "PENDING_PAYMENT";
            case ORDER_STATUS_PAID -> "PAID";
            case ORDER_STATUS_COMPLETED -> "COMPLETED";
            case ORDER_STATUS_CANCELLED -> "CANCELLED";
            default -> "PENDING_PAYMENT";
        };
    }

    default OrderStatus stringToOrderStatus(String status) {
        if (status == null) return OrderStatus.ORDER_STATUS_UNSPECIFIED;
        return switch (status) {
            case "PENDING_PAYMENT" -> OrderStatus.ORDER_STATUS_PENDING_PAYMENT;
            case "PAID" -> OrderStatus.ORDER_STATUS_PAID;
            case "COMPLETED" -> OrderStatus.ORDER_STATUS_COMPLETED;
            case "CANCELLED" -> OrderStatus.ORDER_STATUS_CANCELLED;
            default -> OrderStatus.ORDER_STATUS_UNSPECIFIED;
        };
    }

    default String orderTypeToString(OrderType type) {
        if (type == null) return "UNSPECIFIED";
        return switch (type) {
            case ORDER_TYPE_HOTEL -> "HOTEL";
            case ORDER_TYPE_ATTRACTION -> "ATTRACTION";
            case ORDER_TYPE_FLIGHT -> "FLIGHT";
            case ORDER_TYPE_TRAIN -> "TRAIN";
            default -> "UNSPECIFIED";
        };
    }

    default OrderType stringToOrderType(String type) {
        if (type == null) return OrderType.ORDER_TYPE_UNSPECIFIED;
        return switch (type) {
            case "HOTEL" -> OrderType.ORDER_TYPE_HOTEL;
            case "ATTRACTION" -> OrderType.ORDER_TYPE_ATTRACTION;
            case "FLIGHT" -> OrderType.ORDER_TYPE_FLIGHT;
            case "TRAIN" -> OrderType.ORDER_TYPE_TRAIN;
            default -> OrderType.ORDER_TYPE_UNSPECIFIED;
        };
    }

    default Timestamp epochSecondToTimestamp(long epochSecond) {
        return Timestamp.newBuilder().setSeconds(epochSecond).build();
    }

    default long timestampToEpochSecond(Timestamp ts) {
        return (ts == null) ? 0L : ts.getSeconds();
    }

    default Struct mapToStruct(Map<String, Object> map) {
        if (map == null || map.isEmpty()) return null;
        try {
            String json = new com.fasterxml.jackson.databind.ObjectMapper().writeValueAsString(map);
            Struct.Builder builder = Struct.newBuilder();
            JsonFormat.parser().ignoringUnknownFields().merge(json, builder);
            return builder.build();
        } catch (Exception e) {
            return null;
        }
    }
}
