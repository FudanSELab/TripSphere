package org.tripsphere.product.domain.model;

import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.Set;
import java.util.stream.Collectors;
import lombok.Builder;
import lombok.Getter;
import org.tripsphere.product.domain.exception.DuplicateSkuNameException;
import org.tripsphere.product.domain.exception.InvalidSpuStateException;

@Getter
@Builder
public class Spu {
    private String id;
    private String name;
    private String description;
    private ResourceType resourceType;
    private String resourceId;
    private List<String> images;
    private SpuStatus status;
    private Map<String, Object> attributes;

    @Builder.Default
    private List<Sku> skus = new ArrayList<>();

    public static Spu create(
            String id,
            String name,
            String description,
            ResourceType resourceType,
            String resourceId,
            List<String> images,
            Map<String, Object> attributes,
            List<Sku> skus) {
        Spu spu = Spu.builder()
                .id(id)
                .name(name)
                .description(description)
                .resourceType(resourceType)
                .resourceId(resourceId)
                .images(images)
                .status(SpuStatus.DRAFT)
                .attributes(attributes)
                .build();
        if (skus != null && !skus.isEmpty()) {
            spu.addSkus(skus);
        }
        return spu;
    }

    public Optional<Sku> findSkuById(String skuId) {
        if (skus == null) return Optional.empty();
        return skus.stream().filter(sku -> skuId.equals(sku.getId())).findFirst();
    }

    public List<Sku> findSkusByIds(Set<String> skuIds) {
        if (skus == null) return List.of();
        return skus.stream().filter(sku -> skuIds.contains(sku.getId())).toList();
    }

    public void applyPartialUpdate(Spu partial, List<String> fieldPaths) {
        for (String path : fieldPaths) {
            switch (path) {
                case "name" -> this.name = partial.getName();
                case "description" -> this.description = partial.getDescription();
                case "resource_type" -> this.resourceType = partial.getResourceType();
                case "resource_id" -> this.resourceId = partial.getResourceId();
                case "images" -> this.images = partial.getImages();
                case "attributes" -> this.attributes = partial.getAttributes();
                default -> {}
            }
        }
    }

    public void publish() {
        if (this.status != SpuStatus.DRAFT && this.status != SpuStatus.OFF_SHELF) {
            throw new InvalidSpuStateException(id, status.name(), "publish");
        }
        this.status = SpuStatus.ON_SHELF;
    }

    public void unpublish() {
        if (this.status != SpuStatus.ON_SHELF) {
            throw new InvalidSpuStateException(id, status.name(), "unpublish");
        }
        this.status = SpuStatus.OFF_SHELF;
    }

    public void addSku(Sku sku) {
        sku.setSpuId(this.id);
        boolean duplicate = this.skus.stream().anyMatch(s -> s.getName().equals(sku.getName()));
        if (duplicate) {
            throw new DuplicateSkuNameException(sku.getName());
        }
        this.skus.add(sku);
    }

    public void addSkus(List<Sku> skus) {
        skus.forEach(sku -> sku.setSpuId(this.id));
        Set<String> skuNames = skus.stream().map(Sku::getName).collect(Collectors.toSet());
        if (skuNames.size() != skus.size()) {
            throw new DuplicateSkuNameException();
        }
        Set<String> existingSkuNames = this.skus.stream().map(Sku::getName).collect(Collectors.toSet());
        if (!Collections.disjoint(existingSkuNames, skuNames)) {
            throw new DuplicateSkuNameException();
        }
        this.skus.addAll(skus);
    }
}
