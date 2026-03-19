package org.tripsphere.inventory.config;

import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.boot.context.properties.bind.DefaultValue;

@ConfigurationProperties(prefix = "inventory")
public record InventoryProperties(
        @DefaultValue("900") int defaultLockTimeoutSeconds,
        @DefaultValue("50") int lockExpiryBatchSize) {}
