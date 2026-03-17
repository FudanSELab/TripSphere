package org.tripsphere.product.adapter.outbound.mongodb.document;

import java.util.Map;
import lombok.Data;
import org.tripsphere.product.domain.model.Money;

@Data
public class SkuDocument {
    private String id;
    private String name;
    private String spuId;
    private String description;
    private String status;
    private Map<String, Object> attributes;
    private Money basePrice;
}
