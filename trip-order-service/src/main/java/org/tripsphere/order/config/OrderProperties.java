package org.tripsphere.order.config;

import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.boot.context.properties.bind.DefaultValue;

@ConfigurationProperties(prefix = "order")
public record OrderProperties(
        @DefaultValue("900") int expireSeconds,
        @DefaultValue("10") int dedupWindowSeconds,
        @DefaultValue("50") int expiryBatchSize) {}
