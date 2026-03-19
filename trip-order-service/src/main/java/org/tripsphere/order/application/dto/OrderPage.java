package org.tripsphere.order.application.dto;

import java.util.List;
import org.tripsphere.order.domain.model.Order;

public record OrderPage(List<Order> orders, int totalPages, boolean hasNext, int currentPage) {}
