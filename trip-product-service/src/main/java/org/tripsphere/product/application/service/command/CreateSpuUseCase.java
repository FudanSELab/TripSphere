package org.tripsphere.product.application.service.command;

import java.util.List;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.tripsphere.product.application.dto.CreateSpuCommand;
import org.tripsphere.product.domain.model.Sku;
import org.tripsphere.product.domain.model.Spu;
import org.tripsphere.product.domain.repository.SpuRepository;

@Slf4j
@Service
@RequiredArgsConstructor
public class CreateSpuUseCase {
    private final SpuRepository spuRepository;

    public Spu execute(CreateSpuCommand command) {
        log.debug("Creating SPU: {}", command.name());

        List<Sku> skus = command.skus() != null
                ? command.skus().stream()
                        .map(CreateSpuCommand.CreateSkuCommand::toDomain)
                        .toList()
                : List.of();

        Spu spu = Spu.create(
                command.name(),
                command.description(),
                command.resourceType(),
                command.resourceId(),
                command.images(),
                command.attributes(),
                skus);

        Spu saved = spuRepository.save(spu);
        log.info("Created SPU with id: {}", saved.getId());
        return saved;
    }
}
