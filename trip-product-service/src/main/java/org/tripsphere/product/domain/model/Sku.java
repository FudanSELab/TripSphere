package org.tripsphere.product.domain.model;

import com.github.f4b6a3.uuid.UuidCreator;
import java.util.Map;
import lombok.Builder;
import lombok.Getter;

@Getter
@Builder
public class Sku {
    private String id;
    private String name;
    private String spuId;
    private String description;
    private SkuStatus status;
    private Map<String, Object> attributes;
    private Money basePrice;

    public static Sku create(
            String name, String description, SkuStatus status, Map<String, Object> attributes, Money basePrice) {
        return Sku.builder()
                .id(UuidCreator.getTimeOrderedEpoch().toString())
                .name(name)
                .description(description)
                .status(status != null ? status : SkuStatus.ACTIVE)
                .attributes(attributes)
                .basePrice(basePrice)
                .build();
    }

    public void activate() {
        if (this.status == SkuStatus.ACTIVE) {
            throw new IllegalStateException("SKU is already active");
        }
        this.status = SkuStatus.ACTIVE;
    }

    public void deactivate() {
        if (this.status == SkuStatus.INACTIVE) {
            throw new IllegalStateException("SKU is already inactive");
        }
        this.status = SkuStatus.INACTIVE;
    }

    void setSpuId(String spuId) {
        this.spuId = spuId;
    }
}
