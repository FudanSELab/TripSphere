package org.tripsphere.inventory.infrastructure.config;

import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.boot.context.properties.bind.DefaultValue;
import org.tripsphere.inventory.application.port.InventoryConfigPort;

@ConfigurationProperties(prefix = "inventory")
public record InventoryProperties(
        @DefaultValue("900") int defaultLockTimeoutSeconds,
        @DefaultValue("50") int lockExpiryBatchSize) implements InventoryConfigPort {}
