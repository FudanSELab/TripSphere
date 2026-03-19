package org.tripsphere.order.application.dto;

import java.util.List;
import java.util.Map;

public record SpuInfo(
        String id,
        String name,
        String description,
        String resourceType,
        String resourceId,
        List<String> images,
        Map<String, Object> attributes) {}
