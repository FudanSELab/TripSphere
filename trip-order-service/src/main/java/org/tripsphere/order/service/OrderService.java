package org.tripsphere.order.service;

import java.util.Optional;
import org.springframework.data.domain.Page;
import org.tripsphere.order.v1.ContactInfo;
import org.tripsphere.order.v1.CreateOrderItem;
import org.tripsphere.order.v1.Order;
import org.tripsphere.order.v1.OrderSource;
import org.tripsphere.order.v1.OrderStatus;
import org.tripsphere.order.v1.OrderType;

public interface OrderService {

    Order createOrder(
            String userId,
            java.util.List<CreateOrderItem> items,
            ContactInfo contact,
            OrderSource source);

    Optional<Order> getOrder(String orderId);

    Page<Order> listUserOrders(
            String userId, OrderStatus status, OrderType type, int pageSize, String pageToken);

    Order cancelOrder(String orderId, String reason);

    Order confirmPayment(String orderId, String paymentMethod);
}
