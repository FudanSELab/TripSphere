package org.tripsphere.order.application.dto;

import java.util.Map;
import org.tripsphere.order.domain.model.Money;

public record SkuInfo(
        String id, String spuId, String name, boolean active, Money basePrice, Map<String, Object> attributes) {}
