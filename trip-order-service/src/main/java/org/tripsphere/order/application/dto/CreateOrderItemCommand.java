package org.tripsphere.order.application.dto;

import java.time.LocalDate;

public record CreateOrderItemCommand(String skuId, LocalDate date, LocalDate endDate, int quantity) {}
