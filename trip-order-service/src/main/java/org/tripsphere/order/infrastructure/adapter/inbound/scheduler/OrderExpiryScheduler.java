package org.tripsphere.order.infrastructure.adapter.inbound.scheduler;

import java.time.Instant;
import java.util.Set;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;
import org.tripsphere.order.application.port.OrderCachePort;
import org.tripsphere.order.application.service.command.CancelOrderUseCase;
import org.tripsphere.order.infrastructure.config.OrderProperties;

@Slf4j
@Component
@RequiredArgsConstructor
public class OrderExpiryScheduler {

    private final OrderCachePort cachePort;
    private final CancelOrderUseCase cancelOrderUseCase;
    private final OrderProperties properties;

    @Scheduled(fixedDelay = 30000)
    public void cancelExpiredOrders() {
        long now = Instant.now().getEpochSecond();
        Set<String> expiredOrderIds = cachePort.getExpiredOrderIds(now, properties.expiryBatchSize());

        if (expiredOrderIds == null || expiredOrderIds.isEmpty()) {
            return;
        }

        log.info("Found {} expired orders to cancel", expiredOrderIds.size());

        for (String orderId : expiredOrderIds) {
            try {
                cancelOrderUseCase.execute(orderId, "Payment timeout - auto cancelled");
                log.info("Auto-cancelled expired order: {}", orderId);
            } catch (Exception e) {
                log.error("Failed to cancel expired order: {}", orderId, e);
                cachePort.removeOrderExpiry(orderId);
            }
        }
    }
}
