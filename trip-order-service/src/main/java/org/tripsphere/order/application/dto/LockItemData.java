package org.tripsphere.order.application.dto;

import java.time.LocalDate;

public record LockItemData(String skuId, LocalDate date, int quantity) {}
