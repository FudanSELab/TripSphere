package org.tripsphere.order.adapter.outbound.grpc;

import java.time.LocalDate;
import java.util.List;
import lombok.extern.slf4j.Slf4j;
import net.devh.boot.grpc.client.inject.GrpcClient;
import org.springframework.stereotype.Component;
import org.tripsphere.common.v1.Date;
import org.tripsphere.inventory.v1.*;
import org.tripsphere.order.application.dto.DailyInventoryInfo;
import org.tripsphere.order.application.dto.LockItemData;
import org.tripsphere.order.application.port.InventoryPort;
import org.tripsphere.order.domain.model.Money;

@Slf4j
@Component
public class InventoryGrpcAdapter implements InventoryPort {

    @GrpcClient("trip-inventory-service")
    private InventoryServiceGrpc.InventoryServiceBlockingStub inventoryStub;

    @Override
    public String lockInventory(List<LockItemData> items, String orderId, int timeoutSeconds) {
        log.debug("Locking inventory for order: {}, items: {}", orderId, items.size());
        List<LockItem> protoItems = items.stream()
                .map(item -> LockItem.newBuilder()
                        .setSkuId(item.skuId())
                        .setDate(toProtoDate(item.date()))
                        .setQuantity(item.quantity())
                        .build())
                .toList();

        LockInventoryResponse response = inventoryStub.lockInventory(LockInventoryRequest.newBuilder()
                .addAllItems(protoItems)
                .setOrderId(orderId)
                .setLockTimeoutSeconds(timeoutSeconds)
                .build());
        return response.getLock().getLockId();
    }

    @Override
    public void confirmLock(String lockId) {
        log.debug("Confirming inventory lock: {}", lockId);
        inventoryStub.confirmLock(
                ConfirmLockRequest.newBuilder().setLockId(lockId).build());
    }

    @Override
    public void releaseLock(String lockId, String reason) {
        log.debug("Releasing inventory lock: {}, reason: {}", lockId, reason);
        inventoryStub.releaseLock(ReleaseLockRequest.newBuilder()
                .setLockId(lockId)
                .setReason(reason)
                .build());
    }

    @Override
    public List<DailyInventoryInfo> queryInventoryCalendar(String skuId, LocalDate startDate, LocalDate endDate) {
        log.debug("Querying inventory calendar: sku={}, from={}, to={}", skuId, startDate, endDate);
        QueryInventoryCalendarResponse response =
                inventoryStub.queryInventoryCalendar(QueryInventoryCalendarRequest.newBuilder()
                        .setSkuId(skuId)
                        .setStartDate(toProtoDate(startDate))
                        .setEndDate(toProtoDate(endDate))
                        .build());
        return response.getEntriesList().stream()
                .map(this::toDailyInventoryInfo)
                .toList();
    }

    private DailyInventoryInfo toDailyInventoryInfo(DailyInventory proto) {
        LocalDate date = toLocalDate(proto.getDate());
        Money price = Money.zero();
        if (proto.hasPrice()) {
            price = new Money(
                    proto.getPrice().getCurrency().isEmpty()
                            ? "CNY"
                            : proto.getPrice().getCurrency(),
                    proto.getPrice().getUnits(),
                    proto.getPrice().getNanos());
        }
        return new DailyInventoryInfo(proto.getSkuId(), date, price);
    }

    private Date toProtoDate(LocalDate date) {
        if (date == null) return Date.getDefaultInstance();
        return Date.newBuilder()
                .setYear(date.getYear())
                .setMonth(date.getMonthValue())
                .setDay(date.getDayOfMonth())
                .build();
    }

    private LocalDate toLocalDate(Date proto) {
        if (proto == null) return null;
        return LocalDate.of(proto.getYear(), proto.getMonth(), proto.getDay());
    }
}
