package org.tripsphere.inventory.domain.model;

import java.time.LocalDate;
import lombok.Builder;
import lombok.Getter;

@Getter
@Builder
public class InventoryLockItem {
    private String id;
    private String lockId;
    private String skuId;
    private LocalDate invDate;
    private int quantity;

    public static InventoryLockItem create(String id, String lockId, String skuId, LocalDate invDate, int quantity) {
        return InventoryLockItem.builder()
                .id(id)
                .lockId(lockId)
                .skuId(skuId)
                .invDate(invDate)
                .quantity(quantity)
                .build();
    }
}
