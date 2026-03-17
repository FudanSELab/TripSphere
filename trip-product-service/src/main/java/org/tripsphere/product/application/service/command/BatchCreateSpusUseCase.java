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
public class BatchCreateSpusUseCase {
    private final SpuRepository spuRepository;

    public List<Spu> execute(List<CreateSpuCommand> commands) {
        log.debug("Batch creating {} SPUs", commands.size());

        List<Spu> spus = commands.stream()
                .map(cmd -> {
                    List<Sku> skus = cmd.skus() != null
                            ? cmd.skus().stream()
                                    .map(CreateSpuCommand.CreateSkuCommand::toDomain)
                                    .toList()
                            : List.of();
                    return Spu.create(
                            cmd.name(),
                            cmd.description(),
                            cmd.resourceType(),
                            cmd.resourceId(),
                            cmd.images(),
                            cmd.attributes(),
                            skus);
                })
                .toList();

        List<Spu> saved = spuRepository.saveAll(spus);
        log.info("Batch created {} SPUs", saved.size());
        return saved;
    }
}
