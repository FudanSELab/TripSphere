package org.tripsphere.product.model;

import java.time.Instant;
import java.util.List;
import java.util.Map;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;
import org.springframework.data.annotation.CreatedDate;
import org.springframework.data.annotation.Id;
import org.springframework.data.annotation.LastModifiedDate;
import org.springframework.data.mongodb.core.mapping.Document;

@Data
@Builder
@AllArgsConstructor
@NoArgsConstructor
@Document(collection = "spus")
public class SpuDoc {
    @Id private String id;
    private String name;
    private String description;
    private String resourceType;
    private String resourceId;
    private List<String> images;
    private String status;
    private Map<String, Object> attributes;
    private List<SkuDoc> skus;
    @CreatedDate private Instant createdAt;
    @LastModifiedDate private Instant updatedAt;
}
