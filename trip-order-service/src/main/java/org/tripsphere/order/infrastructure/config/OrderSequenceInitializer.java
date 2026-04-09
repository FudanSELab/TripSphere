package org.tripsphere.order.infrastructure.config;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.boot.ApplicationArguments;
import org.springframework.boot.ApplicationRunner;
import org.springframework.stereotype.Component;
import org.tripsphere.order.application.port.OrderRepository;

@Slf4j
@Component
@RequiredArgsConstructor
public class OrderSequenceInitializer implements ApplicationRunner {

    private final OrderRepository orderRepository;

    @Override
    public void run(ApplicationArguments args) {
        try {
            orderRepository.createSequenceIfNotExists();
            log.info("Order sequence initialized successfully");
        } catch (Exception e) {
            log.warn("Failed to initialize order sequence: {}", e.getMessage());
        }
    }
}
