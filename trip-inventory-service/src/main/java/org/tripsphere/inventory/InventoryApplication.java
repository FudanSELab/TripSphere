package org.tripsphere.inventory;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.springframework.cloud.client.discovery.EnableDiscoveryClient;
import org.springframework.scheduling.annotation.EnableScheduling;
import org.tripsphere.inventory.config.InventoryProperties;

@SpringBootApplication
@EnableDiscoveryClient
@EnableScheduling
@EnableConfigurationProperties(InventoryProperties.class)
public class InventoryApplication {
    public static void main(String[] args) {
        SpringApplication.run(InventoryApplication.class, args);
    }
}
