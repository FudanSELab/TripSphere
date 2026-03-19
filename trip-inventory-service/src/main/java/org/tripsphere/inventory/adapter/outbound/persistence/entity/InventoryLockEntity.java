package org.tripsphere.inventory.adapter.outbound.persistence.entity;

import com.github.f4b6a3.uuid.UuidCreator;
import jakarta.persistence.*;
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
        name = "inventory_lock",
        indexes = {@Index(name = "idx_status_expire", columnList = "status, expireAt")})
public class InventoryLockEntity {

    @Id
    @Column(length = 36, nullable = false)
    private String lockId;

    @Column(nullable = false, unique = true, length = 64)
    private String orderId;

    @Column(nullable = false, length = 16)
    @Builder.Default
    private String status = "LOCKED";

    @Column(nullable = false)
    private long createdAt;

    @Column(nullable = false)
    private long expireAt;

    @PrePersist
    public void generateId() {
        if (this.lockId == null) {
            this.lockId = UuidCreator.getTimeOrderedEpoch().toString();
        }
    }
}
