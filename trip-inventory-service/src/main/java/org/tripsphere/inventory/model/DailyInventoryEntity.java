package org.tripsphere.inventory.model;

import com.github.f4b6a3.uuid.UuidCreator;
import jakarta.persistence.*;
import java.time.Instant;
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
        name = "daily_inventory",
        uniqueConstraints =
                @UniqueConstraint(
                        name = "uk_sku_date",
                        columnNames = {"skuId", "invDate"}))
public class DailyInventoryEntity {

    @Id
    @Column(length = 36, nullable = false)
    private String id;

    @Column(nullable = false, length = 64)
    private String skuId;

    @Column(nullable = false)
    private LocalDate invDate;

    @Column(nullable = false)
    @Builder.Default
    private int totalQty = 0;

    @Column(nullable = false)
    @Builder.Default
    private int availableQty = 0;

    @Column(nullable = false)
    @Builder.Default
    private int lockedQty = 0;

    @Column(nullable = false)
    @Builder.Default
    private int soldQty = 0;

    @Column(nullable = false, length = 3)
    @Builder.Default
    private String priceCurrency = "CNY";

    @Column(nullable = false)
    @Builder.Default
    private long priceUnits = 0;

    @Column(nullable = false)
    @Builder.Default
    private int priceNanos = 0;

    @Column(nullable = false)
    @Builder.Default
    private Instant updatedAt = Instant.now();

    @PrePersist
    private void beforeInsert() {
        if (this.id == null) {
            this.id = UuidCreator.getTimeOrderedEpoch().toString();
        }
        this.updatedAt = Instant.now();
    }

    @PreUpdate
    private void beforeUpdate() {
        this.updatedAt = Instant.now();
    }
}
