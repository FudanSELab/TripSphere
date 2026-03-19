package org.tripsphere.inventory.application.dto;

import java.time.LocalDate;
import java.util.List;

public record LockInventoryCommand(List<LockItemCommand> items, String orderId, int lockTimeoutSeconds) {

    public record LockItemCommand(String skuId, LocalDate date, int quantity) {}
}
