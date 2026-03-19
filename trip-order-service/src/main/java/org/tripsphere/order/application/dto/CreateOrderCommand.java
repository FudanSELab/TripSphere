package org.tripsphere.order.application.dto;

import java.util.List;
import org.tripsphere.order.domain.model.ContactInfo;
import org.tripsphere.order.domain.model.OrderSource;

public record CreateOrderCommand(
        String userId, List<CreateOrderItemCommand> items, ContactInfo contact, OrderSource source) {}
