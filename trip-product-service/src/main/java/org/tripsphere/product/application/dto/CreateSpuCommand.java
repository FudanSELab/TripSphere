package org.tripsphere.product.application.dto;

import java.util.List;
import java.util.Map;
import org.tripsphere.product.domain.model.Money;
import org.tripsphere.product.domain.model.ResourceType;
import org.tripsphere.product.domain.model.Sku;
import org.tripsphere.product.domain.model.SkuStatus;
import org.tripsphere.product.domain.model.Spu;

public record CreateSpuCommand(
        String name,
        String description,
        ResourceType resourceType,
        String resourceId,
        List<String> images,
        Map<String, Object> attributes,
        List<CreateSkuCommand> skus) {

    public record CreateSkuCommand(
            String name, String description, SkuStatus status, Map<String, Object> attributes, Money basePrice) {

        public Sku toDomain() {
            return Sku.create(name, description, status, attributes, basePrice);
        }
    }

    public static CreateSpuCommand from(Spu spu) {
        List<CreateSkuCommand> skuCommands = spu.getSkus() != null
                ? spu.getSkus().stream()
                        .map(s -> new CreateSkuCommand(
                                s.getName(), s.getDescription(), s.getStatus(), s.getAttributes(), s.getBasePrice()))
                        .toList()
                : List.of();
        return new CreateSpuCommand(
                spu.getName(),
                spu.getDescription(),
                spu.getResourceType(),
                spu.getResourceId(),
                spu.getImages(),
                spu.getAttributes(),
                skuCommands);
    }
}
