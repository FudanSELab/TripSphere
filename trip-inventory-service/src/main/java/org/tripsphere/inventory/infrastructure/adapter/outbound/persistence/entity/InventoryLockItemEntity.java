package org.tripsphere.inventory.infrastructure.adapter.outbound.persistence.entity;

import com.github.f4b6a3.uuid.UuidCreator;
import jakarta.persistence.*;
import java.time.LocalDate;
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
        name = "inventory_lock_item",
        indexes = {@Index(name = "idx_lock_id", columnList = "lockId")})
public class InventoryLockItemEntity {

    @Id
    @Column(length = 36, nullable = false)
    private String id;

    @Column(nullable = false, length = 64)
    private String lockId;

    @Column(nullable = false, length = 64)
    private String skuId;

    @Column(nullable = false)
    private LocalDate invDate;

    @Column(nullable = false)
    private int quantity;

    @PrePersist
    public void generateId() {
        if (this.id == null) {
            this.id = UuidCreator.getTimeOrderedEpoch().toString();
        }
    }
}
