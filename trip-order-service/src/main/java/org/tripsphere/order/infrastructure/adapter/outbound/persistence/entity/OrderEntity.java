package org.tripsphere.order.infrastructure.adapter.outbound.persistence.entity;

import jakarta.persistence.*;
import java.util.List;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@Builder
@AllArgsConstructor
@NoArgsConstructor
@Entity
@Table(
        name = "orders",
        indexes = {
            @Index(name = "idx_user_id", columnList = "userId"),
            @Index(name = "idx_status", columnList = "status"),
            @Index(name = "idx_user_status", columnList = "userId, status")
        })
public class OrderEntity {

    @Id
    @Column(length = 64)
    private String id;

    @Column(nullable = false, unique = true, length = 32)
    private String orderNo;

    @Column(nullable = false, length = 64)
    private String userId;

    @Column(nullable = false, length = 24)
    @Builder.Default
    private String status = "PENDING_PAYMENT";

    @Column(nullable = false, length = 3)
    @Builder.Default
    private String totalCurrency = "CNY";

    @Column(nullable = false)
    @Builder.Default
    private long totalUnits = 0;

    @Column(nullable = false)
    @Builder.Default
    private int totalNanos = 0;

    @Column(length = 64)
    private String contactName;

    @Column(length = 20)
    private String contactPhone;

    @Column(length = 128)
    private String contactEmail;

    @Column(length = 16)
    private String sourceChannel;

    @Column(length = 64)
    private String sourceAgentId;

    @Column(length = 64)
    private String sourceSession;

    @Column(nullable = false, length = 16, columnDefinition = "VARCHAR(16) DEFAULT 'UNSPECIFIED'")
    @Builder.Default
    private String type = "UNSPECIFIED";

    @Column(length = 64)
    private String resourceId;

    @Column(length = 256)
    private String cancelReason;

    private Long expireAt;

    @Column(nullable = false)
    private long createdAt;

    @Column(nullable = false)
    private long updatedAt;

    private Long paidAt;

    private Long cancelledAt;

    @Transient
    private List<OrderItemEntity> items;
}
