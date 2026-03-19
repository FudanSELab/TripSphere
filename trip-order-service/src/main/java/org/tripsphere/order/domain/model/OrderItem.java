package org.tripsphere.order.domain.model;

import java.time.LocalDate;
import java.util.Map;
import lombok.Builder;
import lombok.Getter;

@Getter
@Builder
public class OrderItem {
    private String id;
    private String orderId;
    private String spuId;
    private String skuId;
    private String productName;
    private String skuName;
    private String resourceType;
    private String resourceId;
    private String spuImage;
    private String spuDescription;
    private Map<String, Object> skuAttributes;
    private LocalDate itemDate;
    private LocalDate endDate;
    private int quantity;
    private Money unitPrice;
    private Money subtotal;
    private String invLockId;
}
