package org.tripsphere.inventory.application.service.command;

import java.util.List;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.tripsphere.inventory.application.dto.SetDailyInventoryCommand;
import org.tripsphere.inventory.domain.model.DailyInventory;

@Slf4j
@Service
@RequiredArgsConstructor
public class BatchSetDailyInventoryUseCase {

    private final SetDailyInventoryUseCase setDailyInventoryUseCase;

    @Transactional
    public List<DailyInventory> execute(List<SetDailyInventoryCommand> commands) {
        log.debug("Batch setting {} daily inventory records", commands.size());
        return commands.stream().map(setDailyInventoryUseCase::execute).toList();
    }
}
