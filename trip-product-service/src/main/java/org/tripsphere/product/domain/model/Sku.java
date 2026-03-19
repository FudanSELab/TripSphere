package org.tripsphere.product.domain.model;

import java.util.Map;
import lombok.Builder;
import lombok.Getter;
import org.tripsphere.product.domain.exception.InvalidSkuStateException;

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
            String id,
            String name,
            String description,
            SkuStatus status,
            Map<String, Object> attributes,
            Money basePrice) {
        return Sku.builder()
                .id(id)
                .name(name)
                .description(description)
                .status(status != null ? status : SkuStatus.ACTIVE)
                .attributes(attributes)
                .basePrice(basePrice)
                .build();
    }

    public void activate() {
        if (this.status == SkuStatus.ACTIVE) {
            throw new InvalidSkuStateException(id, status.name(), "activate");
        }
        this.status = SkuStatus.ACTIVE;
    }

    public void deactivate() {
        if (this.status == SkuStatus.INACTIVE) {
            throw new InvalidSkuStateException(id, status.name(), "deactivate");
        }
        this.status = SkuStatus.INACTIVE;
    }

    void setSpuId(String spuId) {
        this.spuId = spuId;
    }
}
