package org.tripsphere.order.application.dto;

import java.time.LocalDate;
import org.tripsphere.order.domain.model.Money;

public record DailyInventoryInfo(String skuId, LocalDate date, Money price) {}
