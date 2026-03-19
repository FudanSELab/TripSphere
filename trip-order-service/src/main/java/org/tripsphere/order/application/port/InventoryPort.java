package org.tripsphere.order.application.port;

import java.time.LocalDate;
import java.util.List;
import org.tripsphere.order.application.dto.DailyInventoryInfo;
import org.tripsphere.order.application.dto.LockItemData;

public interface InventoryPort {

    String lockInventory(List<LockItemData> items, String orderId, int timeoutSeconds);

    void confirmLock(String lockId);

    void releaseLock(String lockId, String reason);

    List<DailyInventoryInfo> queryInventoryCalendar(String skuId, LocalDate startDate, LocalDate endDate);
}
