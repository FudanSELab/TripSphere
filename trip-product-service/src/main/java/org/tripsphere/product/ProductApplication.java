package org.tripsphere.product;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.context.properties.EnableConfigurationProperties;
import org.springframework.cloud.client.discovery.EnableDiscoveryClient;
import org.tripsphere.product.infrastructure.config.ProductProperties;

@SpringBootApplication
@EnableDiscoveryClient
@EnableConfigurationProperties(ProductProperties.class)
public class ProductApplication {
    public static void main(String[] args) {
        SpringApplication.run(ProductApplication.class, args);
    }
}
