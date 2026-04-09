package org.tripsphere.product.application.service.query;

import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.function.Function;
import java.util.stream.Collectors;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.tripsphere.product.application.exception.InvalidArgumentException;
import org.tripsphere.product.application.exception.NotFoundException;
import org.tripsphere.product.application.port.SpuRepository;
import org.tripsphere.product.domain.model.Sku;
import org.tripsphere.product.domain.model.Spu;

@Slf4j
@Service
@RequiredArgsConstructor
public class BatchGetSkusUseCase {
    private final SpuRepository spuRepository;

    public List<Sku> execute(List<String> ids) {
        if (ids == null) {
            throw InvalidArgumentException.required("ids");
        }
        if (ids.isEmpty()) {
            return List.of();
        }

        Set<String> requestedIds = new HashSet<>(ids);
        List<Spu> spus = spuRepository.findBySkuIds(ids);

        List<Sku> found = new ArrayList<>();
        for (Spu spu : spus) {
            found.addAll(spu.findSkusByIds(requestedIds));
        }

        Map<String, Sku> skusById = found.stream().collect(Collectors.toMap(Sku::getId, Function.identity()));

        List<String> missingIds =
                ids.stream().filter(id -> !skusById.containsKey(id)).toList();
        if (!missingIds.isEmpty()) {
            throw new NotFoundException("SKUs with IDs " + missingIds + " not found");
        }

        return ids.stream().map(skusById::get).toList();
    }
}
