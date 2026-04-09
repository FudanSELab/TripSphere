package org.tripsphere.product.application.service.query;

import java.util.List;
import java.util.Map;
import java.util.function.Function;
import java.util.stream.Collectors;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;
import org.tripsphere.product.application.exception.InvalidArgumentException;
import org.tripsphere.product.application.exception.NotFoundException;
import org.tripsphere.product.application.port.SpuRepository;
import org.tripsphere.product.domain.model.Spu;

@Slf4j
@Service
@RequiredArgsConstructor
public class BatchGetSpusUseCase {
    private final SpuRepository spuRepository;

    public List<Spu> execute(List<String> ids) {
        if (ids == null) {
            throw InvalidArgumentException.required("ids");
        }
        if (ids.isEmpty()) {
            return List.of();
        }
        List<Spu> spus = spuRepository.findAllById(ids);
        // Check if all SPUs are found
        Map<String, Spu> spusById = spus.stream().collect(Collectors.toMap(Spu::getId, Function.identity()));
        List<String> missingIds =
                ids.stream().filter(id -> !spusById.containsKey(id)).toList();
        if (!missingIds.isEmpty()) {
            throw new NotFoundException("SPUs with IDs " + missingIds + " not found");
        }
        // Return the SPUs in the order of the IDs
        return ids.stream().map(spusById::get).toList();
    }
}
