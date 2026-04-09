package org.tripsphere.order.application.dto;

import org.tripsphere.order.domain.model.OrderStatus;
import org.tripsphere.order.domain.model.OrderType;

public record ListOrdersQuery(String userId, OrderStatus status, OrderType type, int pageSize, int page) {}
