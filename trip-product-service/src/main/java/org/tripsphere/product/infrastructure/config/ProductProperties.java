package org.tripsphere.product.infrastructure.config;

import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.boot.context.properties.bind.DefaultValue;
import org.tripsphere.product.application.port.ProductConfigPort;

@ConfigurationProperties(prefix = "product")
public record ProductProperties(
        @DefaultValue("20") int defaultPageSize,
        @DefaultValue("100") int maxPageSize) implements ProductConfigPort {}
