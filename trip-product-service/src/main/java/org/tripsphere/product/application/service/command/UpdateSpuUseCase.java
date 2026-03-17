package org.tripsphere.product.application.service.command;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.tripsphere.product.application.dto.UpdateSpuCommand;
import org.tripsphere.product.application.exception.NotFoundException;
import org.tripsphere.product.domain.model.Spu;
import org.tripsphere.product.domain.repository.SpuRepository;

@Slf4j
@Service
@RequiredArgsConstructor
public class UpdateSpuUseCase {
    private final SpuRepository spuRepository;

    public Spu execute(UpdateSpuCommand command) {
        log.debug("Updating SPU id={}, fields={}", command.id(), command.fieldPaths());

        Spu existing =
                spuRepository.findById(command.id()).orElseThrow(() -> new NotFoundException("SPU", command.id()));

        if (!command.fieldPaths().isEmpty()) {
            Spu partial = Spu.builder()
                    .name(command.name())
                    .description(command.description())
                    .resourceType(command.resourceType())
                    .resourceId(command.resourceId())
                    .images(command.images())
                    .attributes(command.attributes())
                    .build();
            existing.applyPartialUpdate(partial, command.fieldPaths());
        }

        Spu saved = spuRepository.save(existing);
        log.info("Updated SPU with id: {}", saved.getId());
        return saved;
    }
}
