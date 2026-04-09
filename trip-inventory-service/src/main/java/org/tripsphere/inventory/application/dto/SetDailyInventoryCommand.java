package org.tripsphere.inventory.application.dto;

import java.time.LocalDate;
import org.tripsphere.inventory.domain.model.Money;

public record SetDailyInventoryCommand(String skuId, LocalDate date, int totalQuantity, Money price) {}
