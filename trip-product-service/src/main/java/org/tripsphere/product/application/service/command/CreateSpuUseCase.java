package org.tripsphere.product.application.service.command;

import com.github.f4b6a3.uuid.UuidCreator;
import java.util.List;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.tripsphere.product.application.dto.CreateSpuCommand;
import org.tripsphere.product.application.port.SpuRepository;
import org.tripsphere.product.domain.model.Sku;
import org.tripsphere.product.domain.model.Spu;

@Slf4j
@Service
@RequiredArgsConstructor
public class CreateSpuUseCase {
    private final SpuRepository spuRepository;

    public Spu execute(CreateSpuCommand command) {
        log.debug("Creating SPU: {}", command.name());

        Spu spu = buildSpu(command);
        Spu saved = spuRepository.save(spu);

        log.info("Created SPU with id: {}", saved.getId());
        return saved;
    }

    Spu buildSpu(CreateSpuCommand command) {
        List<Sku> skus = command.skus() != null
                ? command.skus().stream().map(this::buildSku).toList()
                : List.of();

        return Spu.create(
                generateId(),
                command.name(),
                command.description(),
                command.resourceType(),
                command.resourceId(),
                command.images(),
                command.attributes(),
                skus);
    }

    private Sku buildSku(CreateSpuCommand.CreateSkuCommand cmd) {
        return Sku.create(generateId(), cmd.name(), cmd.description(), cmd.status(), cmd.attributes(), cmd.basePrice());
    }

    private String generateId() {
        return UuidCreator.getTimeOrderedEpoch().toString();
    }
}
