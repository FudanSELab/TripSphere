package org.tripsphere.inventory.repository;

import jakarta.persistence.LockModeType;
import java.time.LocalDate;
import java.util.List;
import java.util.Optional;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Lock;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.tripsphere.inventory.model.DailyInventoryEntity;

public interface DailyInventoryRepository extends JpaRepository<DailyInventoryEntity, String> {

    Optional<DailyInventoryEntity> findBySkuIdAndInvDate(String skuId, LocalDate invDate);

    @Lock(LockModeType.PESSIMISTIC_WRITE)
    @Query(
            "SELECT d FROM DailyInventoryEntity d"
                    + " WHERE d.skuId = :skuId AND d.invDate = :invDate")
    Optional<DailyInventoryEntity> findBySkuIdAndInvDateForUpdate(
            @Param("skuId") String skuId, @Param("invDate") LocalDate invDate);

    List<DailyInventoryEntity> findBySkuIdAndInvDateBetweenOrderByInvDateAsc(
            String skuId, LocalDate startDate, LocalDate endDate);
}
