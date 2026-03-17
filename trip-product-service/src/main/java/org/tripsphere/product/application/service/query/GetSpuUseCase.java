package org.tripsphere.product.application.service.query;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.tripsphere.product.application.exception.InvalidArgumentException;
import org.tripsphere.product.application.exception.NotFoundException;
import org.tripsphere.product.domain.model.Spu;
import org.tripsphere.product.domain.repository.SpuRepository;

@Slf4j
@Service
@RequiredArgsConstructor
public class GetSpuUseCase {
    private final SpuRepository spuRepository;

    public Spu execute(String id) {
        if (id == null || id.isBlank()) {
            throw InvalidArgumentException.required("id");
        }
        return spuRepository.findById(id).orElseThrow(() -> new NotFoundException("SPU", id));
    }
}
