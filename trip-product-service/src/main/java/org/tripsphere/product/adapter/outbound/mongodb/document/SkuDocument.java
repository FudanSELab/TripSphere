package org.tripsphere.product.adapter.outbound.mongodb.document;

import java.util.Map;
import lombok.Data;
import org.springframework.data.mongodb.core.mapping.Field;

@Data
public class SkuDocument {
    @Field("id")
    private String id;

    private String name;
    private String spuId;
    private String description;
    private String status;
    private Map<String, Object> attributes;
    private MoneyDocument basePrice;
}
