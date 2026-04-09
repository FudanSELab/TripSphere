package org.tripsphere.product.infrastructure.adapter.outbound.mongodb.document;

import java.util.List;
import java.util.Map;
import lombok.Data;
import org.springframework.data.annotation.Id;
import org.springframework.data.mongodb.core.mapping.Document;

@Data
@Document(collection = "spus")
public class SpuDocument {
    @Id
    private String id;

    private String name;
    private String description;
    private String resourceType;
    private String resourceId;
    private List<String> images;
    private String status;
    private Map<String, Object> attributes;
    private List<SkuDocument> skus;
}
