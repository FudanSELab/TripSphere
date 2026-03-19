package org.tripsphere.product.config;

import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.boot.context.properties.bind.DefaultValue;

@ConfigurationProperties(prefix = "product")
public record ProductProperties(
        @DefaultValue("20") int defaultPageSize,
        @DefaultValue("100") int maxPageSize) {}
