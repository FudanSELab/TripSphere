package org.tripsphere.product.application.dto;

import java.util.List;
import java.util.Map;
import org.tripsphere.product.domain.model.Money;
import org.tripsphere.product.domain.model.ResourceType;
import org.tripsphere.product.domain.model.SkuStatus;

public record CreateSpuCommand(
        String name,
        String description,
        ResourceType resourceType,
        String resourceId,
        List<String> images,
        Map<String, Object> attributes,
        List<CreateSkuCommand> skus) {

    public record CreateSkuCommand(
            String name, String description, SkuStatus status, Map<String, Object> attributes, Money basePrice) {}
}
