package org.tripsphere.product.application.dto;

import java.util.List;
import java.util.Map;
import org.tripsphere.product.domain.model.ResourceType;

public record UpdateSpuCommand(
        String id,
        List<String> fieldPaths,
        String name,
        String description,
        ResourceType resourceType,
        String resourceId,
        List<String> images,
        Map<String, Object> attributes) {}
