package org.tripsphere.product.application.service.query;

import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.tripsphere.product.application.exception.InvalidArgumentException;
import org.tripsphere.product.application.exception.NotFoundException;
import org.tripsphere.product.application.port.SpuRepository;
import org.tripsphere.product.domain.model.Sku;

@Slf4j
@Service
@RequiredArgsConstructor
public class GetSkuUseCase {
    private final SpuRepository spuRepository;

    public Sku execute(String skuId) {
        if (skuId == null || skuId.isBlank()) {
            throw InvalidArgumentException.required("id");
        }
        return spuRepository
                .findBySkuId(skuId)
                .flatMap(spu -> spu.findSkuById(skuId))
                .orElseThrow(() -> new NotFoundException("SKU", skuId));
    }
}
