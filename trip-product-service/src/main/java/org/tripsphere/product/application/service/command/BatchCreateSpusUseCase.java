package org.tripsphere.product.application.service.command;

import java.util.List;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.tripsphere.product.application.dto.CreateSpuCommand;
import org.tripsphere.product.application.port.SpuRepository;
import org.tripsphere.product.domain.model.Spu;

@Slf4j
@Service
@RequiredArgsConstructor
public class BatchCreateSpusUseCase {
    private final SpuRepository spuRepository;
    private final CreateSpuUseCase createSpuUseCase;

    public List<Spu> execute(List<CreateSpuCommand> commands) {
        log.debug("Batch creating {} SPUs", commands.size());

        List<Spu> spus = commands.stream().map(createSpuUseCase::buildSpu).toList();

        List<Spu> saved = spuRepository.saveAll(spus);
        log.info("Batch created {} SPUs", saved.size());
        return saved;
    }
}
