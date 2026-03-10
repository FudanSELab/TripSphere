package org.tripsphere.product.model;

import java.util.Map;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;
import org.springframework.data.mongodb.core.mapping.Field;

@Data
@Builder
@AllArgsConstructor
@NoArgsConstructor
public class SkuDoc {
    @Field("id")
    private String id;

    private String name;
    private String description;
    private String status;
    private Map<String, Object> attributes;
    private Money basePrice;
}
