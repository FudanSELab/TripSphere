package org.tripsphere.inventory.application.dto;

import org.tripsphere.inventory.domain.model.Money;

public record CheckAvailabilityResult(boolean available, int availableQuantity, Money price) {}
